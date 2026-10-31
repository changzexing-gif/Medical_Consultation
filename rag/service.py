from __future__ import annotations

import asyncio
import re
import time
from pathlib import Path

from core.config import settings
from core.monitoring import Event, monitor
from rag.cache import TTLCache
from rag.embeddings import BGEEmbedder, bge_embedder
from rag.indexer import MedicalIndexer
from rag.models import Evidence, SearchResult


def _terms(text: str) -> set[str]:
    chinese = set(re.findall(r"[\u4e00-\u9fff]{2,6}", text))
    ascii_terms = set(re.findall(r"[a-zA-Z0-9]{2,}", text.lower()))
    return chinese | ascii_terms


class RetrievalService:
    """生产化检索：自动索引、BGE 向量召回、词项混合重排、缓存、异步入口。"""

    def __init__(
        self, embedder: BGEEmbedder = bge_embedder, path: Path = settings.chroma_path,
        cache: TTLCache[SearchResult] | None = None,
    ):
        self.embedder = embedder
        self.indexer = MedicalIndexer(embedder, path)
        self.cache = cache or TTLCache(settings.cache_ttl_seconds)

    def _collection(self):
        collection = self.indexer._collection()
        if collection.count() == 0:
            self.indexer.build()
        return collection

    def search(self, query: str, top_k: int = settings.retrieval_top_k, *, query_id: str = "", user_id: str = "anonymous") -> SearchResult:
        clean_query = " ".join(query.split()).strip()
        key = f"{top_k}:{clean_query}"
        cached = self.cache.get(key)
        if cached is not None:
            return SearchResult(cached.query, cached.evidences, cached.latency_ms, True, cached.model)
        started = time.perf_counter()
        hit_count = 0
        success = True
        failure_mode = None
        try:
            collection = self._collection()
            query_vector = self.embedder.encode_query(clean_query)
            recall_k = max(top_k * 3, 10)
            raw = collection.query(
                query_embeddings=[query_vector], n_results=min(recall_k, collection.count()),
                include=["documents", "metadatas", "distances"],
            )
            candidates: list[Evidence] = []
            query_terms = _terms(clean_query)
            for item_id, document, metadata, distance in zip(
                raw["ids"][0], raw["documents"][0], raw["metadatas"][0], raw["distances"][0]
            ):
                vector_score = max(0.0, 1.0 - float(distance))
                doc_terms = _terms(document + " " + metadata.get("title", ""))
                lexical = len(query_terms & doc_terms) / max(1, len(query_terms))
                score = 0.85 * vector_score + 0.15 * lexical
                candidates.append(Evidence(
                    id=item_id, source=metadata.get("source", "未知来源"),
                    title=metadata.get("title", ""), content=document,
                    relevance=round(score, 4), page=str(metadata.get("page", "")),
                    url=metadata.get("url", ""),
                ))
            evidences = sorted(candidates, key=lambda e: e.relevance, reverse=True)[:top_k]
            hit_count = len(evidences)
            latency = (time.perf_counter() - started) * 1000
            result = SearchResult(clean_query, evidences, latency, False, self.embedder.model_name)
            self.cache.set(key, result)
            return result
        except Exception as exc:
            success = False
            failure_mode = monitor.classify_failure(exc)
            raise
        finally:
            monitor.record(Event(
                "retrieval", agent="retrieval", latency_ms=(time.perf_counter() - started) * 1000,
                success=success, failure_mode=failure_mode, user_id=user_id, query_id=query_id,
                metadata={"hit_count": hit_count, "top_k": top_k, "model": self.embedder.model_name},
            ))

    async def asearch(self, query: str, top_k: int = settings.retrieval_top_k, **kwargs) -> SearchResult:
        return await asyncio.to_thread(self.search, query, top_k, **kwargs)


retrieval_service = RetrievalService()
