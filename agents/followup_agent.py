from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from agents.base import BaseAgent
from agents.types import AgentResult, UserContext


class FollowupAgent(BaseAgent):
    """新增 Agent：生成不构成自动诊疗的自我监测与复诊计划。"""

    name = "followup"

    def _execute(self, user_input: str, context: UserContext, upstream: dict[str, AgentResult], query_id: str) -> dict[str, Any]:
        risk = upstream.get("risk")
        urgency = risk.data.get("urgency_level", "低") if risk and risk.success else "待评估"
        hours = 0 if urgency in ("极高", "高") else 24 if urgency == "中" else 72
        return {
            "review_by": "立即" if hours == 0 else (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M"),
            "monitor": ["记录体温和症状变化", "按需记录心率、血压", "若出现新的危险信号立即就医"],
            "return_precautions": ["呼吸困难", "意识改变", "持续或加重胸痛", "肢体无力或言语不清"],
            "urgency_basis": urgency,
        }
