from agents.types import UserContext
from core.workflow import MedicalWorkflow
from rag.models import Evidence, SearchResult


class FakeRetrievalService:
    def search(self, query, top_k=5, **kwargs):
        return SearchResult(
            query, [Evidence("1", "胸痛指南", "急性胸痛", "胸痛伴大汗应拨打120", .95)],
            2.0, False, "fake-bge",
        )


def test_langgraph_workflow_and_arbitration():
    workflow = MedicalWorkflow(FakeRetrievalService())
    state = workflow.invoke("胸口压榨样疼痛伴大汗并放射左臂", UserContext("workflow-test"))
    assert list(state["results"]) == ["consultation", "retrieval", "triage", "medication", "risk", "followup"]
    assert state["final"]["urgency_level"] == "极高"
    assert state["final"]["medication"]["recommended_drugs"] == []
    assert state["final"]["evidences"][0]["source"] == "胸痛指南"
