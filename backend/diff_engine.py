"""
自然语言指令解析 + UI-diff 应用
实现 Add / Remove / Update / Reorder 操作，并支持跨页面 role-based 传播
"""
from __future__ import annotations

import copy
import re
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Any

from data.defaults import get_default_component_library


ADD_KEYWORDS = ["添加", "增加", "新增", "加上", "add", "insert", "增加一个"]
REMOVE_KEYWORDS = ["删除", "移除", "remove", "去掉", "不要"]
MOVE_KEYWORDS = ["移动", "挪", "拖到", "移到", "置于", "move"]
RESIZE_KEYWORDS = ["缩小", "窄", "宽", "扩大", "放大", "加宽", "narrow", "widen", "bigger", "smaller"]
CONSISTENCY_KEYWORDS = ["所有", "保持一致", "跨页面", "一致", "同步", "同样"]

COMPONENT_HINTS = {
    "AlertTable": ["告警", "alert", "警报"],
    "GlobalFilterBar": ["过滤", "filter", "筛选"],
    "TrendChart": ["趋势", "trend", "折线", "chart"],
    "InsightSummary": ["洞察", "insight"],
    "KPIOverview": ["kpi", "指标", "概览", "summary"],
    "RunStatus": ["运行", "状态", "run", "列表"],
    "BacklogTable": ["需求", "backlog"],
    "RiskBoard": ["风险", "risk"],
    "ActionLog": ["日志", "log", "行动"],
    "PersonaFocus": ["persona", "角色"],
}

SECTION_HINTS = {
    "header": ["顶部", "头部", "上方", "header"],
    "sidebar": ["右侧", "侧边", "左侧", "sidebar"],
    "footer": ["底部", "footer"],
    "main": ["中间", "主区域", "主区", "内容", "main", "列表"],
}

PAGE_HINTS = {
    "plan": ["配置", "plan", "准备"],
    "observe": ["监控", "monitor", "运行", "observe"],
    "analyze": ["分析", "复盘", "分析"],
    "overview": ["概览", "overview"],
    "alerts_ops": ["告警"],
    "capacity": ["容量"],
    "execution": ["执行"],
    "review": ["复盘"],
}


class UIDiffEngine:
    """指令解析 + diff 应用"""

    def __init__(self, component_library: List[dict] | None = None):
        self.component_library = component_library or get_default_component_library()

    # ----------------- 指令解析 -----------------

    def instruction_to_diff(self, instruction: str, schema: dict) -> Tuple[dict, List[str]]:
        text = instruction.strip()
        normalized = text.lower()
        warnings: List[str] = []
        scope = "same_role_across_pages" if self._detect_scope(normalized) else "current_page"

        target_page = self._detect_page(normalized, schema)
        target_section = self._detect_section(normalized)
        component_hint = self._detect_component_hint(normalized)

        operations = []
        intent = None

        if any(keyword in text for keyword in ADD_KEYWORDS):
            intent = "add"
            component_payload = self._build_component_payload(component_hint, normalized)
            if not component_payload:
                warnings.append("未能匹配到合适的组件，自动 fallback 为 KPI 卡片")
                component_payload = self._build_component_payload("KPIOverview", normalized, fallback=True)

            section_id = target_section or self._fallback_section(schema, target_page)
            operations.append({
                "op": "AddNode",
                "targetSectionId": section_id,
                "component": component_payload,
                "pageId": target_page,
            })

        elif any(keyword in text for keyword in REMOVE_KEYWORDS):
            intent = "remove"
            component_id = self._find_component_id(schema, component_hint, target_page)
            if component_id:
                operations.append({
                    "op": "RemoveNode",
                    "componentId": component_id,
                    "pageId": target_page,
                })
            else:
                warnings.append("没有找到要删除的组件，忽略此次操作")

        elif any(keyword in text for keyword in MOVE_KEYWORDS):
            intent = "move"
            component_id = self._find_component_id(schema, component_hint, target_page)
            dest_section = target_section or self._fallback_section(schema, target_page)
            if component_id and dest_section:
                operations.append({
                    "op": "UpdateProps",
                    "componentId": component_id,
                    "changes": {
                        "targetSectionId": dest_section,
                    }
                })
            else:
                warnings.append("移动操作失败：未找到组件或目标区域")

        elif any(keyword in text for keyword in RESIZE_KEYWORDS):
            intent = "resize"
            component_id = self._find_component_id(schema, component_hint, target_page)
            delta = self._parse_resize_delta(text)
            if component_id and delta:
                operations.append({
                    "op": "UpdateProps",
                    "componentId": component_id,
                    "changes": {
                        "layout": {"colSpanDelta": delta},
                        "style": {"emphasis": "highlight" if delta > 0 else "normal"},
                    }
                })
            else:
                warnings.append("没有识别到需要调整宽度的组件")

        else:
            intent = "update"
            component_id = self._find_component_id(schema, component_hint, target_page)
            if component_id:
                style = {}
                if "对比" in text or "contrast" in normalized:
                    style["emphasis"] = "highlight"
                if "密度" in text or "density" in normalized:
                    style["density"] = "low" if "轻" in text else "high"
                operations.append({
                    "op": "UpdateProps",
                    "componentId": component_id,
                    "changes": {"style": style}
                })
            else:
                warnings.append("未识别到可更新的组件；请尝试更具体的描述")

        return {
            "scope": scope,
            "intent": intent,
            "operations": operations,
            "summary": text,
            "pageId": target_page,
        }, warnings

    def _detect_scope(self, normalized_instruction: str) -> bool:
        return any(keyword in normalized_instruction for keyword in CONSISTENCY_KEYWORDS)

    def _detect_page(self, normalized_instruction: str, schema: dict) -> str | None:
        for stage_id, hints in PAGE_HINTS.items():
            if any(hint in normalized_instruction for hint in hints):
                return f"page_{stage_id}"
        match = re.search(r"page\s*([abc])", normalized_instruction)
        if match:
            idx = ord(match.group(1).lower()) - ord("a")
            pages = schema.get("pages", [])
            if 0 <= idx < len(pages):
                return pages[idx]["id"]
        return schema.get("pages", [{}])[0].get("id") if schema.get("pages") else None

    def _detect_section(self, normalized_instruction: str) -> str | None:
        for role, hints in SECTION_HINTS.items():
            if any(hint in normalized_instruction for hint in hints):
                return role
        return None

    def _detect_component_hint(self, normalized_instruction: str) -> str | None:
        for role, hints in COMPONENT_HINTS.items():
            if any(hint in normalized_instruction for hint in hints):
                return role
        return None

    def _build_component_payload(self, hint_role: str | None, instruction: str, fallback: bool = False) -> dict | None:
        target_role = hint_role or ("KPIOverview" if fallback else None)
        candidate = None
        if target_role:
            candidate = next(
                (comp for comp in self.component_library if comp.get("role") == target_role),
                None
            )
        if not candidate and self.component_library:
            candidate = self.component_library[0]
        if not candidate:
            return None
        new_id = f"{candidate['role']}_{uuid.uuid4().hex[:4]}"
        return {
            "id": new_id,
            "role": candidate.get("role"),
            "type": candidate.get("type"),
            "dataRole": candidate.get("data_role"),
            "interaction": candidate.get("interaction", []),
            "layout": {
                "colSpan": candidate.get("layout_span", 4),
                "order": 99,
            },
            "bindings": {"source": "instruction"},
            "style": candidate.get("style", {}),
            "infoRefs": [],
            "meta": {
                "description": f"由指令创建：{instruction[:60]}",
            },
        }

    def _find_component_id(self, schema: dict, hint_role: str | None, page_id: str | None) -> str | None:
        pages = schema.get("pages", [])
        for page in pages:
            if page_id and page["id"] != page_id:
                continue
            for section in page.get("sections", []):
                for component in section.get("components", []):
                    if hint_role and component.get("role") == hint_role:
                        return component["id"]
                    if not hint_role:
                        return component["id"]
        return None

    def _fallback_section(self, schema: dict, page_id: str | None) -> str | None:
        pages = schema.get("pages", [])
        for page in pages:
            if page_id and page["id"] != page_id:
                continue
            for section in page.get("sections", []):
                if section["role"] in {"main", "header"}:
                    return section["id"]
        return pages[0]["sections"][0]["id"] if pages and pages[0]["sections"] else None

    def _parse_resize_delta(self, text: str) -> int | None:
        if any(keyword in text for keyword in ["缩小", "窄", "narrow", "小"]):
            return -2
        if any(keyword in text for keyword in ["放大", "加宽", "宽", "大", "widen", "bigger"]):
            return 2
        return None

    # ----------------- diff 应用 -----------------

    def apply_diff(self, schema: dict, diff: dict) -> Tuple[dict, List[str], List[str]]:
        if not diff.get("operations"):
            return schema, [], ["没有可执行的操作"]

        updated = copy.deepcopy(schema)
        log: List[str] = []
        warnings: List[str] = []
        touched_components: List[str] = []

        for op in diff["operations"]:
            operator = op.get("op")
            if operator == "AddNode":
                message, component_ids = self._apply_add(updated, op)
                if message:
                    log.append(message)
                touched_components.extend(component_ids)
            elif operator == "RemoveNode":
                removed_id = self._apply_remove(updated, op)
                if removed_id:
                    touched_components.append(removed_id)
                    log.append(f"Removed {removed_id}")
                else:
                    warnings.append("要删除的组件不存在")
            elif operator == "UpdateProps":
                changed_ids = self._apply_update(updated, op, diff.get("scope"))
                if changed_ids:
                    touched_components.extend(changed_ids)
                    log.append(f"更新 {', '.join(changed_ids)}")
            elif operator == "ReorderChildren":
                order_log = self._apply_reorder(updated, op)
                log.append(order_log)

        self._resolve_layout_conflicts(updated)
        updated["version"] = updated.get("version", 1) + 1
        updated.setdefault("metadata", {})["lastUpdatedAt"] = datetime.utcnow().isoformat()
        updated.setdefault("metadata", {})["lastModifiedComponents"] = touched_components

        return updated, log, warnings

    def _apply_add(self, schema: dict, op: dict) -> Tuple[str, List[str]]:
        page_id = op.get("pageId")
        target_section_id = op.get("targetSectionId")
        component = copy.deepcopy(op.get("component"))
        component["id"] = component.get("id") or f"component_{uuid.uuid4().hex[:4]}"
        component.setdefault("layout", {})["order"] = component["layout"].get("order", 99)
        component.setdefault("meta", {})["lastInstruction"] = "add"

        section = self._find_section(schema, page_id, target_section_id)
        if not section:
            return "未找到目标区域，新增失败", []
        section.setdefault("components", []).append(component)
        return (f"新增 {component['role'] or component['type']} -> {section['id']}", [component["id"]])

    def _apply_remove(self, schema: dict, op: dict) -> str | None:
        component_id = op.get("componentId")
        for page in schema.get("pages", []):
            for section in page.get("sections", []):
                components = section.get("components", [])
                for idx, component in enumerate(components):
                    if component["id"] == component_id:
                        components.pop(idx)
                        return component_id
        return None

    def _apply_update(self, schema: dict, op: dict, scope: str | None) -> List[str]:
        component_id = op.get("componentId")
        target_components = []

        base_component = self._find_component(schema, component_id)
        if not base_component:
            return target_components

        if scope == "same_role_across_pages" and base_component.get("role"):
            target_components = self._find_components_by_role(schema, base_component["role"])
        else:
            target_components = [base_component]

        for component in target_components:
            changes = op.get("changes", {})
            if "targetSectionId" in changes:
                self._move_component(schema, component["id"], changes["targetSectionId"])
            if "layout" in changes:
                delta = changes["layout"].get("colSpanDelta")
                if delta:
                    component.setdefault("layout", {})
                    component["layout"]["colSpan"] = max(2, component["layout"].get("colSpan", 4) + delta)
            if "style" in changes:
                component.setdefault("style", {}).update(changes["style"])
            component.setdefault("meta", {})["lastInstruction"] = "update"
            component["meta"]["lastUpdatedAt"] = datetime.utcnow().isoformat()

        return [comp["id"] for comp in target_components]

    def _apply_reorder(self, schema: dict, op: dict) -> str:
        section_id = op.get("sectionId")
        new_order = op.get("newOrder", [])
        section = self._find_section(schema, None, section_id)
        if not section:
            return "Reorder skipped: section not found"

        components = {comp["id"]: comp for comp in section.get("components", [])}
        reordered = []
        for comp_id in new_order:
            if comp_id in components:
                reordered.append(components.pop(comp_id))
        reordered.extend(components.values())
        for order, component in enumerate(reordered, start=1):
            component.setdefault("layout", {})["order"] = order
        section["components"] = reordered
        return f"Reordered {section_id}"

    def _move_component(self, schema: dict, component_id: str, target_section_id: str):
        component = None
        for page in schema.get("pages", []):
            for section in page.get("sections", []):
                comps = section.get("components", [])
                for idx, comp in enumerate(comps):
                    if comp["id"] == component_id:
                        component = comp
                        comps.pop(idx)
                        break
                if component:
                    break
            if component:
                break
        if component:
            section = self._find_section(schema, None, target_section_id)
            if section:
                section.setdefault("components", []).append(component)

    def _resolve_layout_conflicts(self, schema: dict):
        for page in schema.get("pages", []):
            for section in page.get("sections", []):
                components = section.get("components", [])
                if not components:
                    continue
                limit = section.get("layout", {}).get("colSpan", 12)
                total = sum(comp.get("layout", {}).get("colSpan", 4) for comp in components)
                if total <= limit:
                    continue
                overflow = total - limit
                components_sorted = sorted(components, key=lambda c: c.get("layout", {}).get("colSpan", 4), reverse=True)
                for component in components_sorted:
                    if overflow <= 0:
                        break
                    current = component.get("layout", {}).get("colSpan", 4)
                    deduction = min(overflow, max(1, current - 3))
                    component["layout"]["colSpan"] = max(3, current - deduction)
                    overflow -= deduction
                if overflow > 0:
                    section.setdefault("layout", {})["scrollable"] = True

    # ----------------- 查找工具 -----------------

    def _find_section(self, schema: dict, page_id: str | None, section_id_or_role: str | None):
        for page in schema.get("pages", []):
            if page_id and page["id"] != page_id:
                continue
            for section in page.get("sections", []):
                if section["id"] == section_id_or_role or section["role"] == section_id_or_role:
                    return section
        return None

    def _find_component(self, schema: dict, component_id: str):
        for page in schema.get("pages", []):
            for section in page.get("sections", []):
                for component in section.get("components", []):
                    if component["id"] == component_id:
                        return component
        return None

    def _find_components_by_role(self, schema: dict, role: str) -> List[dict]:
        comps = []
        for page in schema.get("pages", []):
            for section in page.get("sections", []):
                for component in section.get("components", []):
                    if component.get("role") == role:
                        comps.append(component)
        return comps
