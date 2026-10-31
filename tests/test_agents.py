from agents.clinical_rules import detect_red_flags, normalize_symptoms
from agents.coordinator import AgentCoordinator
from agents.medication_agent import MedicationAgent
from agents.types import AgentResult, UserContext


def test_symptom_normalization_and_red_flag():
    assert "头痛" in normalize_symptoms("脑壳痛，还发烧38.2度")
    flags = detect_red_flags("胸口压榨样疼痛伴大汗")
    assert any(f["score"] == 100 for f in flags)


def test_medication_allergy_blocks_penicillin():
    context = UserContext("s", allergies=["青霉素严重过敏"])
    upstream = {"consultation": AgentResult("consultation", True, {"symptoms": ["发热"]}, 1)}
    result = MedicationAgent().run("发热", context, upstream)
    assert result.success
    assert any("禁用阿莫西林" in x for x in result.data["contraindications"])


def test_extreme_risk_overrides_medication():
    results = {
        "consultation": AgentResult("consultation", True, {}, 1),
        "risk": AgentResult("risk", True, {"urgency_level": "极高", "recommendation": "立即拨打120"}, 1),
        "medication": AgentResult("medication", True, {"recommended_drugs": [{"name": "测试药"}]}, 1),
        "retrieval": AgentResult("retrieval", True, {"evidences": []}, 1),
    }
    final = AgentCoordinator.arbitrate(results)
    assert final["medication"]["recommended_drugs"] == []
    assert "极高风险" in final["conflicts"][0]


def test_contraindication_overrides_medication():
    results = {
        "consultation": AgentResult("consultation", True, {}, 1),
        "risk": AgentResult("risk", True, {"urgency_level": "中", "recommendation": "门诊"}, 1),
        "medication": AgentResult("medication", True, {
            "recommended_drugs": [{"name": "测试药"}], "contraindications": ["测试禁忌"]
        }, 1),
    }
    final = AgentCoordinator.arbitrate(results)
    assert final["medication"]["recommended_drugs"] == []
    assert "禁忌" in final["conflicts"][0]
