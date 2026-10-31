from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from agents.consultation_agent import ConsultationAgent
from agents.followup_agent import FollowupAgent
from agents.medication_agent import MedicationAgent
from agents.retrieval_agent import RetrievalAgent
from agents.risk_agent import RiskAgent
from agents.triage_agent import TriageAgent
from agents.types import AgentResult, UserContext


class AgentCoordinator:
    """同步协调器：问诊→检索→分诊→(用药∥风险)→随访→仲裁。"""

    def __init__(self, retrieval_service: Any | None = None):
        self.consultation = ConsultationAgent()
        self.retrieval = RetrievalAgent(retrieval_service)
        self.triage = TriageAgent()
        self.medication = MedicationAgent()
        self.risk = RiskAgent()
        self.followup = FollowupAgent()

    def run(self, user_input: str, context: UserContext) -> dict[str, Any]:
        query_id = str(uuid.uuid4())
        results: dict[str, AgentResult] = {}
        results["consultation"] = self.consultation.run(user_input, context, results, query_id)
        results["retrieval"] = self.retrieval.run(user_input, context, results, query_id)
        results["triage"] = self.triage.run(user_input, context, results, query_id)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {
                "medication": pool.submit(self.medication.run, user_input, context, results.copy(), query_id),
                "risk": pool.submit(self.risk.run, user_input, context, results.copy(), query_id),
            }
            for name, future in futures.items():
                results[name] = future.result()
        results["followup"] = self.followup.run(user_input, context, results, query_id)
        return {"query_id": query_id, "results": results, "final": self.arbitrate(results)}

    @staticmethod
    def arbitrate(results: dict[str, AgentResult]) -> dict[str, Any]:
        conflicts: list[str] = []
        risk = results.get("risk")
        medication = results.get("medication")
        retrieval = results.get("retrieval")
        urgency = risk.data.get("urgency_level", "待评估") if risk and risk.success else "待评估"
        med_data = medication.data.copy() if medication and medication.success else {}
        if urgency == "极高":
            med_data["recommended_drugs"] = []
            conflicts.append("极高风险覆盖用药建议：优先立即急诊。")
        elif med_data.get("contraindications") or med_data.get("interactions"):
            med_data["recommended_drugs"] = []
            conflicts.append("检测到禁忌或相互作用：取消自动用药建议，转由医生/药师审核。")
        consultation = results.get("consultation")
        return {
            "urgency_level": urgency,
            "recommendation": risk.data.get("recommendation", "请线下就医") if risk and risk.success else "请线下就医",
            "consultation": consultation.data if consultation and consultation.success else {},
            "medication": med_data,
            "evidences": retrieval.data.get("evidences", []) if retrieval and retrieval.success else [],
            "followup": results.get("followup").data if results.get("followup") and results["followup"].success else {},
            "conflicts": conflicts,
            "disclaimer": "本结果由AI生成，仅用于健康教育，不能替代医生诊断和处方。",
        }
