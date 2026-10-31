from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict


@dataclass
class UserContext:
    session_id: str
    user_id: str = "anonymous"
    age: int | None = None
    sex: str = "未说明"
    allergies: list[str] = field(default_factory=list)
    current_medications: list[str] = field(default_factory=list)
    medical_history: list[str] = field(default_factory=list)
    vitals: dict[str, float] = field(default_factory=dict)
    pregnant: bool = False


@dataclass
class AgentResult:
    agent: str
    success: bool
    data: dict[str, Any]
    latency_ms: float
    error: str | None = None


class WorkflowState(TypedDict, total=False):
    query_id: str
    user_input: str
    context: UserContext
    results: dict[str, AgentResult]
    final: dict[str, Any]
