"""
会话管理模块
负责存储任务上下文、组件库、副本栈和 UI-diff 历史
"""
from __future__ import annotations

import copy
from datetime import datetime
from typing import Dict, Optional, List
import uuid

from data.defaults import get_default_component_library


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "context": None,
            "component_library": get_default_component_library(),
            "schema": None,
            "stage_plan": [],
            "info_queue": [],
            "context_summary": None,
            "diff_history": [],
            "undo_stack": [],
            "last_diff": None,
            "created_at": datetime.utcnow().isoformat(),
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[dict]:
        return self.sessions.get(session_id)

    # --- context / components -------------------------------------------------

    def update_context(self, session_id: str, context: dict, summary: dict):
        session = self.get_session(session_id)
        if session:
            session["context"] = context
            session["context_summary"] = summary

    def set_component_library(self, session_id: str, component_library: List[dict]):
        session = self.get_session(session_id)
        if session:
            session["component_library"] = component_library or get_default_component_library()

    def get_component_library(self, session_id: str) -> List[dict]:
        session = self.get_session(session_id)
        if not session:
            return get_default_component_library()
        return session.get("component_library", get_default_component_library())

    # --- schema / info queue --------------------------------------------------

    def set_schema(
        self,
        session_id: str,
        schema: dict,
        info_queue: Optional[List[dict]] = None,
        stage_plan: Optional[List[dict]] = None,
        push_undo: bool = False,
        reset_undo: bool = False,
    ):
        session = self.get_session(session_id)
        if not session:
            return
        if push_undo and session.get("schema"):
            snapshot = copy.deepcopy(session["schema"])
            session["undo_stack"].append(snapshot)
        if reset_undo:
            session["undo_stack"] = []
        session["schema"] = schema
        if info_queue is not None:
            session["info_queue"] = info_queue
        if stage_plan is not None:
            session["stage_plan"] = stage_plan

    def get_schema(self, session_id: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if session:
            return session.get("schema")
        return None

    def get_stage_plan(self, session_id: str) -> List[dict]:
        session = self.get_session(session_id)
        if session:
            return session.get("stage_plan", [])
        return []

    def get_info_queue(self, session_id: str) -> List[dict]:
        session = self.get_session(session_id)
        if session:
            return session.get("info_queue", [])
        return []

    # --- diff history --------------------------------------------------------

    def append_diff_history(self, session_id: str, entry: dict):
        session = self.get_session(session_id)
        if not session:
            return
        entry_with_id = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            **entry,
        }
        session["diff_history"].append(entry_with_id)
        session["last_diff"] = entry_with_id
        # 控制长度，避免无限增长
        if len(session["diff_history"]) > 40:
            session["diff_history"] = session["diff_history"][-40:]

    def get_diff_history(self, session_id: str) -> List[dict]:
        session = self.get_session(session_id)
        if session:
            return session.get("diff_history", [])
        return []

    def get_last_diff(self, session_id: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if session:
            return session.get("last_diff")
        return None

    # --- undo ----------------------------------------------------------------

    def undo(self, session_id: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if not session or not session.get("undo_stack"):
            return None
        schema = session["undo_stack"].pop()
        session["schema"] = schema
        session["last_diff"] = {
            "id": "undo",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": "撤销上一步",
        }
        return schema

    # --- debug payload -------------------------------------------------------

    def debug_payload(self, session_id: str) -> dict:
        session = self.get_session(session_id) or {}
        return {
            "contextSummary": session.get("context_summary"),
            "infoQueue": session.get("info_queue", []),
            "stagePlan": session.get("stage_plan", []),
            "diffHistory": session.get("diff_history", []),
            "schemaVersion": session.get("schema", {}).get("version") if session.get("schema") else None,
        }
