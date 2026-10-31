from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from agents.types import AgentResult, UserContext


class RetrievalAgent(BaseAgent):
    name = "retrieval"

    def __init__(self, service: Any | None = None):
        self._service = service

    @property
    def service(self) -> Any:
        if self._service is None:
            from rag.service import retrieval_service
            self._service = retrieval_service
        return self._service

    def _execute(self, user_input: str, context: UserContext, upstream: dict[str, AgentResult], query_id: str) -> dict[str, Any]:
        consultation = upstream.get("consultation")
        query_parts = [user_input]
        if consultation and consultation.success:
            query_parts.extend(consultation.data.get("symptoms", []))
            query_parts.extend(d.get("disease", "") for d in consultation.data.get("suspected_diagnosis", []))
        result = self.service.search(" ".join(query_parts), query_id=query_id, user_id=context.user_id)
        return {
            "query": result.query,
            "evidences": [e.to_dict() for e in result.evidences],
            "summary": "；".join(e.content[:120] for e in result.evidences[:3]) or "未检索到足够证据",
            "cache_hit": result.cache_hit,
            "model": result.model,
        }
