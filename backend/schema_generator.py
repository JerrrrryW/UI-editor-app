"""
UI Schema 生成器
根据任务上下文、Persona、组件库和场景模板生成多页面界面族
"""
from __future__ import annotations

import copy
import re
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any

from data.defaults import (
    SCENARIO_LIBRARY,
    DEFAULT_PERSONAS,
    get_scenario,
    get_default_component_library,
)


def _slug(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "item"


def _split_sentences(text: str) -> List[str]:
    """粗粒度拆分句子/条目"""
    if not text:
        return []
    parts = re.split(r"[。.!?；;\n]+", text)
    return [p.strip() for p in parts if p.strip()]


class SchemaGenerator:
    """负责生成 UI Schema 以及上下文摘要"""

    def __init__(self, component_library: List[dict] | None = None):
        self.component_library = component_library or get_default_component_library()

    def summarize_context(self, task_spec: str, persona: dict, scenario_id: str) -> dict:
        """生成上下文摘要，方便在前端确认"""
        persona_summary = {
            "name": persona.get("name"),
            "role": persona.get("role"),
            "focus": persona.get("attention", [])[:3],
            "tone": persona.get("tone"),
        }
        scenario = get_scenario(scenario_id) or SCENARIO_LIBRARY[0]
        task_sentences = _split_sentences(task_spec)[:4]
        component_stats = self._component_stats()
        return {
            "persona": persona_summary,
            "taskHighlights": task_sentences,
            "componentStats": component_stats,
            "scenario": {
                "id": scenario["id"],
                "name": scenario["name"],
                "stageCount": len(scenario["stages"]),
            },
        }

    def plan_stages(self, task_spec: str, scenario_id: str) -> List[dict]:
        """根据场景模板 + task spec 文本，生成功能阶段描述"""
        scenario = get_scenario(scenario_id) or SCENARIO_LIBRARY[0]
        keywords = _split_sentences(task_spec.lower())
        plan = []
        for index, stage in enumerate(scenario["stages"]):
            hint = stage["description"]
            # 简单关键词提示
            matches = [
                sentence for sentence in keywords
                if any(token in sentence for token in [stage["name"], stage["id"]])
            ]
            if matches:
                hint = matches[0][:160]
            plan.append({
                "id": stage["id"],
                "name": stage["name"],
                "description": hint,
                "order": index + 1,
            })
        return plan

    def build_info_queue(
        self, task_spec: str, scenario_id: str, stage_plan: List[dict]
    ) -> List[dict]:
        """构造 PriorityQueue，融合模板信息项与 task spec 解析结果"""
        scenario = get_scenario(scenario_id) or SCENARIO_LIBRARY[0]
        info_items = []
        info_items.extend(copy.deepcopy(scenario["info_items"]))

        stage_map = {stage["id"]: stage for stage in stage_plan}

        # 基于 task spec 生成额外信息项
        sentences = _split_sentences(task_spec)
        for sent in sentences:
            if len(sent) < 8:
                continue
            stage_id = self._infer_stage_from_sentence(sent, stage_plan)
            info_id = f"spec_{_slug(sent)[:20]}"
            info_items.append({
                "id": info_id,
                "description": sent,
                "stage": stage_id,
                "roles": self._infer_roles_from_sentence(sent),
                "priority": 0.55,
            })

        # 去重（以 id 为准，如果 spec 生成与模板冲突则保留优先级高者）
        unique = {}
        for item in info_items:
            if item["id"] not in unique or unique[item["id"]]["priority"] < item["priority"]:
                unique[item["id"]] = item

        queue = sorted(unique.values(), key=lambda x: x["priority"], reverse=True)
        # 添加顺序索引便于展示
        for rank, item in enumerate(queue, start=1):
            item["rank"] = rank
            item["stageName"] = stage_map.get(item["stage"], {}).get("name", item["stage"])
        return queue

    def generate_schema(
        self,
        context: dict,
        stage_plan: List[dict],
        info_queue: List[dict],
    ) -> dict:
        """根据上下文生成完整的 UI Schema"""
        scenario_id = context.get("scenario_id")
        scenario = get_scenario(scenario_id) or SCENARIO_LIBRARY[0]
        component_index = {comp["id"]: comp for comp in self.component_library}

        pages = []
        for stage in scenario["stages"]:
            plan_meta = next((p for p in stage_plan if p["id"] == stage["id"]), stage)
            sections = self._build_sections(
                stage,
                info_queue,
                component_index,
                stage_plan=stage_plan,
                persona=context.get("persona"),
            )
            pages.append({
                "id": f"page_{stage['id']}",
                "name": f"{stage['name']} Page",
                "stage": plan_meta["name"],
                "description": plan_meta["description"],
                "sections": sections,
            })

        return {
            "taskId": context.get("task_id"),
            "version": 1,
            "generatedAt": datetime.utcnow().isoformat(),
            "pages": pages,
            "infoQueue": info_queue,
            "metadata": {
                "taskSpec": context.get("task_spec"),
                "persona": context.get("persona"),
                "scenario": scenario,
                "stagePlan": stage_plan,
            },
        }

    # --- helpers ---------------------------------------------------------

    def _component_stats(self):
        by_type: Dict[str, int] = {}
        by_role: Dict[str, int] = {}
        for comp in self.component_library:
            by_type[comp["type"]] = by_type.get(comp["type"], 0) + 1
            if comp.get("role"):
                by_role[comp["role"]] = by_role.get(comp["role"], 0) + 1
        return {
            "total": len(self.component_library),
            "types": by_type,
            "roles": by_role,
        }

    def _infer_stage_from_sentence(self, sentence: str, stage_plan: List[dict]) -> str:
        sentence = sentence.lower()
        for stage in stage_plan:
            keywords = [
                stage["name"].lower(),
                stage["id"].lower(),
            ]
            if any(keyword in sentence for keyword in keywords):
                return stage["id"]
        return stage_plan[0]["id"] if stage_plan else "plan"

    def _infer_roles_from_sentence(self, sentence: str) -> List[str]:
        mapping = {
            "告警": "alerts",
            "alert": "alerts",
            "指标": "kpi",
            "kpi": "kpi",
            "趋势": "chart",
            "chart": "chart",
            "过滤": "filter",
            "filter": "filter",
            "日志": "log",
            "风险": "risk",
            "persona": "persona",
            "角色": "persona",
        }
        roles = []
        for key, value in mapping.items():
            if key in sentence:
                roles.append(value)
        return roles or ["meta"]

    def _build_sections(
        self,
        stage_template: dict,
        info_queue: List[dict],
        component_index: Dict[str, dict],
        stage_plan: List[dict],
        persona: dict | None = None,
    ) -> List[dict]:
        sections = []
        row_pointer = 1
        pending_row = None
        for section_template in stage_template["sections"]:
            role = section_template["role"]
            if role == "sidebar" and pending_row:
                row = pending_row
                pending_row = None
            else:
                row = row_pointer

            layout = self._section_layout(role, row)

            if role in {"main", "header"}:
                row_pointer += 1
            if role == "main":
                pending_row = row

            components = self._select_components_for_section(
                section_id=f"{stage_template['id']}_{role}_{len(sections)+1}",
                info_ids=section_template.get("info_ids", []),
                max_components=section_template.get("max_components", 2),
                info_queue=info_queue,
                component_index=component_index,
                layout_span=layout["colSpan"],
                section_role=role,
                persona=persona,
            )

            sections.append({
                "id": f"{stage_template['id']}_{role}_{len(sections)+1}",
                "role": role,
                "title": section_template.get("title"),
                "layout": layout,
                "components": components,
            })
        return sections

    def _section_layout(self, role: str, row: int) -> dict:
        """12 列布局的简单启发式"""
        if role == "header":
            return {"row": row, "colStart": 1, "colSpan": 12, "order": row}
        if role == "sidebar":
            return {"row": row, "colStart": 9, "colSpan": 4, "order": row + 2}
        if role == "footer":
            return {"row": row, "colStart": 1, "colSpan": 12, "order": row + 5}
        return {"row": row, "colStart": 1, "colSpan": 8, "order": row + 1}

    def _select_components_for_section(
        self,
        section_id: str,
        info_ids: List[str],
        max_components: int,
        info_queue: List[dict],
        component_index: Dict[str, dict],
        layout_span: int,
        section_role: str,
        persona: dict | None,
    ) -> List[dict]:
        components = []
        info_targets = [
            item for item in info_queue if item["id"] in info_ids
        ]
        used_roles = set()
        for info in info_targets:
            candidates = self._rank_components_for_info(info, component_index)
            for candidate in candidates:
                if len(components) >= max_components:
                    break
                # 避免在 header 中塞入密度高的表格
                if section_role == "header" and candidate.get("type") in {"Table"}:
                    continue
                comp_instance = self._instantiate_component(
                    component=candidate,
                    info=info,
                    section_span=layout_span,
                    order=len(components) + 1,
                )
                if comp_instance["role"] in used_roles and section_role != "main":
                    continue
                components.append(comp_instance)
                used_roles.add(comp_instance["role"])
        # 如果组件不足，用通用 fallback
        while len(components) < max_components:
            fallback = self._fallback_component(section_role, component_index)
            if not fallback:
                break
            components.append(self._instantiate_component(
                fallback,
                info_targets[0] if info_targets else {
                    "id": f"{section_id}_placeholder",
                    "description": "待补充信息",
                    "roles": ["meta"],
                },
                section_span=layout_span,
                order=len(components) + 1,
            ))
        return components

    def _rank_components_for_info(self, info: dict, component_index: Dict[str, dict]) -> List[dict]:
        ranked = []
        roles = info.get("roles", [])
        for component in component_index.values():
            score = 0.0
            info_roles = component.get("info_roles", [])
            if any(role in info_roles for role in roles):
                score += 0.6
            if component.get("role") and component["role"].lower().startswith(info["id"].split("_")[0]):
                score += 0.1
            if component.get("data_role") in info["id"]:
                score += 0.2
            if component.get("type") in {"Table", "Kanban"} and "list" in roles:
                score += 0.1
            if score > 0:
                ranked.append((score, component))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        return [comp for _, comp in ranked]

    def _instantiate_component(
        self,
        component: dict,
        info: dict,
        section_span: int,
        order: int,
    ) -> dict:
        col_span = min(component.get("layout_span", 4), section_span)
        instance_id = f"{component['role']}_{uuid.uuid4().hex[:4]}"
        info_refs = [info["id"]]
        return {
            "id": instance_id,
            "role": component.get("role"),
            "type": component.get("type"),
            "dataRole": component.get("data_role"),
            "interaction": component.get("interaction", []),
            "layout": {
                "colSpan": col_span,
                "order": order,
            },
            "bindings": {"source": info["id"]},
            "style": component.get("style", {}),
            "infoRefs": info_refs,
            "meta": {
                "description": component.get("description"),
                "createdFrom": info.get("description"),
                "density": component.get("density"),
            },
        }

    def _fallback_component(self, section_role: str, component_index: Dict[str, dict]) -> dict | None:
        prefer_roles = {
            "header": ["KPIOverview", "InsightSummary"],
            "main": ["TrendChart", "BacklogTable", "RunStatus"],
            "sidebar": ["GlobalFilterBar", "ActionLog", "PersonaFocus"],
        }
        for role in prefer_roles.get(section_role, []):
            comp = next((c for c in component_index.values() if c.get("role") == role), None)
            if comp:
                return comp
        return next(iter(component_index.values()), None)

