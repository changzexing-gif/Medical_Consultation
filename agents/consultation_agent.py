from __future__ import annotations

import re
from typing import Any

from agents.base import BaseAgent
from agents.clinical_rules import detect_red_flags, likely_diagnoses, normalize_symptoms
from agents.types import AgentResult, UserContext
from core.llm import llm_client
from core.memory import conversation_store


class ConsultationAgent(BaseAgent):
    name = "consultation"

    def _execute(self, user_input: str, context: UserContext, upstream: dict[str, AgentResult], query_id: str) -> dict[str, Any]:
        history = conversation_store.context(context.session_id)
        symptoms = normalize_symptoms(user_input + " " + history)
        flags = detect_red_flags(user_input, context.vitals)
        duration_match = re.search(r"(\d+\s*(?:小时|天|周|个月|年))", user_input)
        followups: list[str] = []
        if not duration_match:
            followups.append("症状持续多久了？是突然还是逐渐出现？")
        if "头痛" in symptoms:
            followups.extend(["头痛部位和程度如何？", "是否有颈部僵硬、意识改变或肢体无力？"])
        if any(x in symptoms for x in ("胸痛", "胸部不适")):
            followups.extend(["是否为压榨感并向左臂或下颌放射？", "是否伴大汗、气促或濒死感？"])
        if not context.allergies:
            followups.append("是否有药物过敏史？")
        data: dict[str, Any] = {
            "chief_complaint": user_input.strip(),
            "symptoms": symptoms,
            "duration": duration_match.group(1) if duration_match else "待补充",
            "red_flags": [f["name"] for f in flags],
            "suspected_diagnosis": likely_diagnoses(symptoms),
            "need_followup": list(dict.fromkeys(followups))[:5],
            "history_turns": len(conversation_store.history(context.session_id).messages) // 2,
            "mode": "rules",
        }
        if llm_client.enabled:
            try:
                data = llm_client.structured(
                    "你是全科问诊助手。只输出JSON，字段为chief_complaint,symptoms,duration,red_flags,suspected_diagnosis,need_followup。不得确诊。",
                    f"历史：{history}\n本轮：{user_input}\n基础信息：{context}",
                    agent=self.name, query_id=query_id, user_id=context.user_id,
                )
                data["mode"] = "llm"
            except Exception as exc:
                data["llm_fallback"] = str(exc)
        summary = "；".join(data.get("symptoms", [])) or "信息不足"
        conversation_store.append(context.session_id, user_input, f"已记录：{summary}")
        return data
