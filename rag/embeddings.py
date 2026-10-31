from __future__ import annotations

import threading
from collections.abc import Iterable

from core.config import settings


class BGEEmbedder:
    """经典 BGE bi-encoder，查询使用官方中文检索指令并归一化向量。"""

    query_instruction = "为这个句子生成表示以用于检索相关文章："

    def __init__(self, model_name: str = settings.bge_model):
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()

    @property
    def model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                    except ImportError as exc:
                        raise RuntimeError("缺少 sentence-transformers，请执行 pip install -r requirements.txt") from exc
                    self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode_documents(self, texts: Iterable[str]) -> list[list[float]]:
        values = list(texts)
        if not values:
            return []
        vectors = self.model.encode(values, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()

    def encode_query(self, query: str) -> list[float]:
        text = self.query_instruction + query.strip()
        return self.model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0].tolist()


bge_embedder = BGEEmbedder()
