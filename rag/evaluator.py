from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any

from rag.service import RetrievalService


@dataclass
class EvalCase:
    query: str
    expected_source_keyword: str
    expected_answer_keywords: list[str]


DEFAULT_CASES = [
    EvalCase("普通感冒应该怎么治疗", "普通感冒", ["对症", "休息"]),
    EvalCase("胸痛伴大汗需要怎么处理", "胸痛", ["急诊", "120"]),
    EvalCase("青霉素过敏能吃阿莫西林吗", "药物过敏", ["禁用", "青霉素"]),
    EvalCase("儿童发热如何使用退热药", "儿童发热", ["体重", "剂量"]),
    EvalCase("头痛发热颈部僵硬危险吗", "头痛", ["脑膜炎", "急诊"]),
]


class RAGEvaluator:
    def __init__(self, service: RetrievalService):
        self.service = service

    def run(self, cases: list[EvalCase] = DEFAULT_CASES, top_k: int = 5) -> dict[str, Any]:
        rows = []
        for case in cases:
            result = self.service.search(case.query, top_k=top_k)
            joined = " ".join(f"{e.title} {e.source} {e.content}" for e in result.evidences)
            source_hit = case.expected_source_keyword in joined
            keyword_recall = sum(k in joined for k in case.expected_answer_keywords) / len(case.expected_answer_keywords)
            reciprocal_rank = 0.0
            for i, evidence in enumerate(result.evidences, 1):
                if case.expected_source_keyword in evidence.source + evidence.title + evidence.content:
                    reciprocal_rank = 1 / i
                    break
            rows.append({
                **asdict(case), "source_hit": source_hit, "keyword_recall": keyword_recall,
                "reciprocal_rank": reciprocal_rank, "latency_ms": result.latency_ms,
                "top_sources": [e.source for e in result.evidences],
            })
        return {
            "cases": rows,
            "hit_rate_at_k": mean(float(r["source_hit"]) for r in rows),
            "mrr": mean(r["reciprocal_rank"] for r in rows),
            "keyword_recall": mean(r["keyword_recall"] for r in rows),
            "avg_latency_ms": mean(r["latency_ms"] for r in rows),
        }
