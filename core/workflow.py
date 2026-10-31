from __future__ import annotations

import uuid
from typing import Any

from langgraph.graph import END, START, StateGraph

from agents.consultation_agent import ConsultationAgent
from agents.coordinator import AgentCoordinator
from agents.followup_agent import FollowupAgent
from agents.medication_agent import MedicationAgent
from agents.retrieval_agent import RetrievalAgent
from agents.risk_agent import RiskAgent
from agents.triage_agent import TriageAgent
from agents.types import AgentResult, UserContext, WorkflowState


class MedicalWorkflow:
    """LangGraph 工作流；节点保持结构化输入输出，便于替换真实模型。"""

    def __init__(self, retrieval_service: Any | None = None):
        self.agents = {
            "consultation": ConsultationAgent(),
            "retrieval": RetrievalAgent(retrieval_service),
            "triage": TriageAgent(),
            "medication": MedicationAgent(),
            "risk": RiskAgent(),
            "followup": FollowupAgent(),
        }
        self.graph = self._build()

    def _node(self, name: str):
        def execute(state: WorkflowState) -> dict[str, Any]:
            results = dict(state.get("results", {}))
            result = self.agents[name].run(
                state["user_input"], state["context"], results, state["query_id"]
            )
            results[name] = result
            return {"results": results}
        return execute

    @staticmethod
    def _finalize(state: WorkflowState) -> dict[str, Any]:
        return {"final": AgentCoordinator.arbitrate(state.get("results", {}))}

    def _build(self):
        builder = StateGraph(WorkflowState)
        for name in self.agents:
            builder.add_node(name, self._node(name))
        builder.add_node("finalize", self._finalize)
        builder.add_edge(START, "consultation")
        builder.add_edge("consultation", "retrieval")
        builder.add_edge("retrieval", "triage")
        builder.add_edge("triage", "medication")
        builder.add_edge("medication", "risk")
        builder.add_edge("risk", "followup")
        builder.add_edge("followup", "finalize")
        builder.add_edge("finalize", END)
        return builder.compile()

    def invoke(self, user_input: str, context: UserContext) -> WorkflowState:
        return self.graph.invoke({
            "query_id": str(uuid.uuid4()), "user_input": user_input,
            "context": context, "results": {},
        })
