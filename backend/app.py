"""
Flask 主应用 - 复杂任务界面生成与自然语言编辑 MVP
提供上下文配置、界面生成、UI-diff 编辑、调试与导出接口
"""
from __future__ import annotations

import io
import json

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from session_manager import SessionManager
from schema_generator import SchemaGenerator
from diff_engine import UIDiffEngine
from data.defaults import (
    SCENARIO_LIBRARY,
    DEFAULT_PERSONAS,
    get_persona,
    get_scenario,
    get_default_component_library,
)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

session_manager = SessionManager()


# ------------------------ 基础信息 ------------------------


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})


@app.route("/api/session", methods=["POST"])
def create_session():
    session_id = session_manager.create_session()
    return jsonify({"success": True, "session_id": session_id})


@app.route("/api/templates", methods=["GET"])
def list_templates():
    return jsonify({
        "success": True,
        "personas": DEFAULT_PERSONAS,
        "scenarios": SCENARIO_LIBRARY,
        "defaultComponents": get_default_component_library(),
    })


# ------------------------ F1 上下文配置 ------------------------


@app.route("/api/context", methods=["POST"])
def configure_context():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    task_spec = data.get("task_spec")
    scenario_id = data.get("scenario_id")
    persona_payload = data.get("persona", {})
    persona_id = data.get("persona_id")
    component_library = _parse_component_library(data.get("component_library"))

    if not session_id or not task_spec:
        return jsonify({"success": False, "error": "缺少 session_id 或任务描述"}), 400

    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "无效的 session"}), 404

    persona = get_persona(persona_id) or {}
    persona.update(persona_payload or {})
    if not persona:
        persona = {"name": "临时 persona", "role": "Designer"}

    scenario = get_scenario(scenario_id) or SCENARIO_LIBRARY[0]
    component_library = component_library or get_default_component_library()

    context = {
        "task_id": session_id,
        "task_spec": task_spec,
        "persona": persona,
        "scenario_id": scenario["id"],
    }

    generator = SchemaGenerator(component_library)
    summary = generator.summarize_context(task_spec, persona, scenario["id"])

    session_manager.update_context(session_id, context, summary)
    session_manager.set_component_library(session_id, component_library)

    return jsonify({
        "success": True,
        "summary": summary,
        "persona": persona,
        "scenario": scenario,
        "componentStats": summary["componentStats"],
    })


# ------------------------ F2 界面生成 ------------------------


@app.route("/api/generate", methods=["POST"])
def generate_ui():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"success": False, "error": "缺少 session_id"}), 400

    session = session_manager.get_session(session_id)
    if not session or not session.get("context"):
        return jsonify({"success": False, "error": "请先配置任务上下文"}), 400

    context = session["context"]
    component_library = session_manager.get_component_library(session_id)
    generator = SchemaGenerator(component_library)

    stage_plan = generator.plan_stages(context["task_spec"], context["scenario_id"])
    info_queue = generator.build_info_queue(context["task_spec"], context["scenario_id"], stage_plan)
    schema = generator.generate_schema(context, stage_plan, info_queue)

    session_manager.set_schema(
        session_id,
        schema,
        info_queue=info_queue,
        stage_plan=stage_plan,
        push_undo=False,
        reset_undo=True,
    )

    return jsonify({
        "success": True,
        "schema": schema,
        "stagePlan": stage_plan,
        "infoQueue": info_queue,
    })


@app.route("/api/schema/<session_id>", methods=["GET"])
def get_schema(session_id: str):
    schema = session_manager.get_schema(session_id)
    if not schema:
        return jsonify({"success": False, "error": "当前会话没有 Schema"}), 404
    return jsonify({
        "success": True,
        "schema": schema,
        "infoQueue": session_manager.get_info_queue(session_id),
        "stagePlan": session_manager.get_stage_plan(session_id),
        "lastDiff": session_manager.get_last_diff(session_id),
    })


# ------------------------ F3/F4 自然语言编辑 -------------------


@app.route("/api/edit", methods=["POST"])
def edit_schema():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    instruction = data.get("instruction", "").strip()

    if not session_id or not instruction:
        return jsonify({"success": False, "error": "缺少 session_id 或指令"}), 400

    schema = session_manager.get_schema(session_id)
    if not schema:
        return jsonify({"success": False, "error": "请先生成界面"}), 400

    component_library = session_manager.get_component_library(session_id)
    engine = UIDiffEngine(component_library)
    diff, parse_warnings = engine.instruction_to_diff(instruction, schema)

    if not diff.get("operations"):
        return jsonify({"success": False, "error": "未识别到可执行的操作", "warnings": parse_warnings}), 400

    new_schema, log, apply_warnings = engine.apply_diff(schema, diff)

    all_warnings = [w for w in (parse_warnings + apply_warnings) if w]

    session_manager.set_schema(session_id, new_schema, push_undo=True)
    session_manager.append_diff_history(session_id, {
        "instruction": instruction,
        "diff": diff,
        "log": log,
        "warnings": all_warnings,
        "scope": diff.get("scope"),
    })

    return jsonify({
        "success": True,
        "schema": new_schema,
        "diff": diff,
        "log": log,
        "warnings": all_warnings,
        "lastDiff": session_manager.get_last_diff(session_id),
    })


@app.route("/api/history/<session_id>", methods=["GET"])
def diff_history(session_id: str):
    history = session_manager.get_diff_history(session_id)
    return jsonify({"success": True, "history": history})


@app.route("/api/undo", methods=["POST"])
def undo_edit():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"success": False, "error": "缺少 session_id"}), 400
    schema = session_manager.undo(session_id)
    if not schema:
        return jsonify({"success": False, "error": "没有更多可撤销的操作"}), 400
    return jsonify({
        "success": True,
        "schema": schema,
        "infoQueue": session_manager.get_info_queue(session_id),
        "lastDiff": session_manager.get_last_diff(session_id),
    })


# ------------------------ F5 Debug & 导出 ----------------------


@app.route("/api/debug/<session_id>", methods=["GET"])
def debug_view(session_id: str):
    return jsonify({"success": True, **session_manager.debug_payload(session_id)})


@app.route("/api/export/<session_id>", methods=["GET"])
def export_schema(session_id: str):
    schema = session_manager.get_schema(session_id)
    if not schema:
        return jsonify({"success": False, "error": "没有可导出的 Schema"}), 404
    buffer = io.BytesIO()
    buffer.write(json.dumps(schema, indent=2, ensure_ascii=False).encode("utf-8"))
    buffer.seek(0)
    filename = f"ui_schema_{session_id[:6]}.json"
    return send_file(
        buffer,
        mimetype="application/json",
        as_attachment=True,
        download_name=filename,
    )


# ------------------------ helpers ---------------------------------


def _parse_component_library(payload):
    if payload is None:
        return None
    if isinstance(payload, list):
        return payload
    if isinstance(payload, str) and payload.strip():
        try:
            data = json.loads(payload)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            return None
    return None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
