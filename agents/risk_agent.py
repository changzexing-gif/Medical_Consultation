from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from agents.clinical_rules import detect_red_flags
from agents.types import AgentResult, UserContext


class RiskAgent(BaseAgent):
    name = "risk"

    def _execute(self, user_input: str, context: UserContext, upstream: dict[str, AgentResult], query_id: str) -> dict[str, Any]:
        flags = detect_red_flags(user_input, context.vitals)
        consultation = upstream.get("consultation")
        if consultation and consultation.success:
            for name in consultation.data.get("red_flags", []):
                if not any(f["name"] == name for f in flags):
                    flags.append({"name": name, "score": 80})
        score = max((f["score"] for f in flags), default=15)
        age = context.age or 0
        if age >= 65:
            score += 8
        if any(x in " ".join(context.medical_history) for x in ("冠心病", "卒中", "肿瘤", "免疫")):
            score += 10
        score = min(score, 100)
        if score >= 95:
            level, recommendation = "极高", "立即拨打120或前往最近急诊；不要自行驾车。"
        elif score >= 75:
            level, recommendation = "高", "建议立即急诊评估。"
        elif score >= 35:
            level, recommendation = "中", "建议24-48小时内到门诊就诊；若加重则立即就医。"
        else:
            level, recommendation = "低", "可短期居家观察并对症护理，持续或加重时门诊就诊。"
        chronic = {
            "hypertension": "需评估" if context.vitals.get("systolic_bp", 0) >= 140 else "信息不足/低提示",
            "diabetes": "需评估" if context.vitals.get("glucose", 0) >= 7 else "信息不足/低提示",
        }
        return {
            "urgency_level": level, "risk_score": score,
            "red_flags_triggered": [f["name"] for f in flags],
            "chronic_risks": chronic, "recommendation": recommendation,
            "self_monitoring": ["每日记录症状变化", "按需测体温", "出现危险信号立即就医"],
        }
