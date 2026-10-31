from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from agents.clinical_rules import detect_red_flags
from agents.types import AgentResult, UserContext


class TriageAgent(BaseAgent):
    """新增 Agent：在完整风险评估前执行快速分诊，优先拦截危急症。"""

    name = "triage"

    def _execute(self, user_input: str, context: UserContext, upstream: dict[str, AgentResult], query_id: str) -> dict[str, Any]:
        flags = detect_red_flags(user_input, context.vitals)
        max_score = max((f["score"] for f in flags), default=0)
        if max_score >= 95:
            level, action = "立即", "停止线上问诊，立即拨打120或前往最近急诊；不要自行驾车。"
        elif max_score >= 80:
            level, action = "紧急", "建议立即前往急诊，由陪同人员护送。"
        elif flags:
            level, action = "优先", "建议当日就医评估。"
        else:
            level, action = "常规", "继续完成问诊与风险评估。"
        return {"triage_level": level, "action": action, "signals": flags, "score": max_score}
