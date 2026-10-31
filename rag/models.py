from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    title: str
    content: str
    relevance: float
    page: str = ""
    url: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SearchResult:
    query: str
    evidences: list[Evidence]
    latency_ms: float
    cache_hit: bool
    model: str
