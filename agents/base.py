from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from agents.types import AgentResult, UserContext
from core.monitoring import Event, monitor


class BaseAgent(ABC):
    name = "base"

    def run(
        self,
        user_input: str,
        context: UserContext,
        upstream: dict[str, AgentResult] | None = None,
        query_id: str = "",
    ) -> AgentResult:
        started = time.perf_counter()
        try:
            data = self._execute(user_input, context, upstream or {}, query_id)
            result = AgentResult(self.name, True, data, (time.perf_counter() - started) * 1000)
        except Exception as exc:
            result = AgentResult(self.name, False, {}, (time.perf_counter() - started) * 1000, str(exc))
        monitor.record(Event(
            "agent_call", agent=self.name, latency_ms=result.latency_ms,
            success=result.success, failure_mode=None if result.success else monitor.classify_failure(Exception(result.error or "")),
            user_id=context.user_id, query_id=query_id, metadata={"session_id": context.session_id},
        ))
        return result

    @abstractmethod
    def _execute(
        self, user_input: str, context: UserContext,
        upstream: dict[str, AgentResult], query_id: str,
    ) -> dict[str, Any]:
        raise NotImplementedError
