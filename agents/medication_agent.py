from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from agents.types import AgentResult, UserContext


INTERACTIONS = {
    frozenset(("华法林", "阿司匹林")): "出血风险显著增加",
    frozenset(("硝酸甘油", "西地那非")): "可导致严重低血压，禁止联用",
    frozenset(("布洛芬", "华法林")): "胃肠道及全身出血风险增加",
}


class MedicationAgent(BaseAgent):
    name = "medication"

    def _execute(self, user_input: str, context: UserContext, upstream: dict[str, AgentResult], query_id: str) -> dict[str, Any]:
        consultation = upstream.get("consultation")
        symptoms = consultation.data.get("symptoms", []) if consultation and consultation.success else []
        recommendations: list[dict[str, str]] = []
        warnings: list[str] = []
        contraindications: list[str] = []

        if any("发热" in s or "头痛" in s for s in symptoms):
            recommendations.append({
                "name": "对乙酰氨基酚", "dose": "成人一次0.5g，必要时每4-6小时一次",
                "max": "24小时不超过2g（本系统采用保守上限）", "purpose": "退热/止痛",
            })
            warnings.append("避免与其他含对乙酰氨基酚的复方感冒药叠加，服药期间避免饮酒。")
            if any("肝" in x for x in context.medical_history):
                contraindications.append("存在肝病史：不应自行使用对乙酰氨基酚，请先咨询医生。")
                recommendations = [r for r in recommendations if r["name"] != "对乙酰氨基酚"]
        if "咳嗽" in symptoms:
            warnings.append("咳嗽病因未明时不建议自行使用抗生素。")

        allergy_text = " ".join(context.allergies)
        if any(x in allergy_text for x in ("青霉素", "阿莫西林")):
            contraindications.append("青霉素类过敏：禁用阿莫西林等青霉素类药物。")
        if context.pregnant:
            warnings.append("妊娠期用药需由产科/药师审核，勿自行用药。")
        if context.age is not None and context.age < 18:
            warnings.append("未成年人需按体重计算剂量，当前页面不提供成人剂量建议。")
            recommendations = []

        drugs = context.current_medications + [r["name"] for r in recommendations]
        interactions = []
        for pair, message in INTERACTIONS.items():
            if pair.issubset(set(drugs)):
                interactions.append({"drugs": " + ".join(sorted(pair)), "severity": "高", "message": message})
        return {
            "recommended_drugs": recommendations,
            "warnings": warnings,
            "interactions": interactions,
            "contraindications": contraindications,
            "education": "任何药物均应核对说明书；如症状加重、出现皮疹或呼吸困难，立即停药并就医。",
            "requires_clinician_review": bool(interactions or contraindications or context.pregnant),
        }
