from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.config import ROOT, settings
from core.monitoring import monitor
from rag.embeddings import BGEEmbedder, bge_embedder


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    metadata: dict[str, Any]


def chunk_text(text: str, chunk_size: int = 420, overlap: int = 60) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    sentences = [s.strip() for s in re.split(r"(?<=[。！？；])", clean) if s.strip()]
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + len(sentence) > chunk_size:
            chunks.append(current)
            current = current[-overlap:] + sentence
        else:
            current += sentence
    if current:
        chunks.append(current)
    return chunks


class MedicalIndexer:
    def __init__(self, embedder: BGEEmbedder = bge_embedder, path: Path = settings.chroma_path):
        self.embedder = embedder
        self.path = Path(path)

    def _collection(self):
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("缺少 chromadb，请执行 pip install -r requirements.txt") from exc
        self.path.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(self.path))
        return client.get_or_create_collection(
            settings.collection_name,
            metadata={"hnsw:space": "cosine", "embedding_model": self.embedder.model_name},
        )

    def load_documents(self, source: Path | None = None) -> list[dict[str, Any]]:
        source = source or ROOT / "data" / "medical_knowledge.json"
        return json.loads(source.read_text(encoding="utf-8"))

    def prepare(self, documents: list[dict[str, Any]]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for doc in documents:
            for index, text in enumerate(chunk_text(doc["content"])):
                raw_id = f'{doc["id"]}:{index}:{text}'
                chunk_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:24]
                metadata = {
                    "document_id": doc["id"], "title": doc["title"],
                    "source": doc["source"], "page": str(doc.get("page", "")),
                    "url": doc.get("url", ""), "category": doc.get("category", "general"),
                    "chunk_index": index,
                }
                chunks.append(Chunk(chunk_id, text, metadata))
        return chunks

    def build(self, documents: list[dict[str, Any]] | None = None, batch_size: int = 32) -> int:
        chunks = self.prepare(documents or self.load_documents())
        collection = self._collection()
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            embeddings = self.embedder.encode_documents(c.text for c in batch)
            collection.upsert(
                ids=[c.id for c in batch], documents=[c.text for c in batch],
                metadatas=[c.metadata for c in batch], embeddings=embeddings,
            )
        monitor.set_index_state(settings.collection_name, collection.count(), self.embedder.model_name)
        return collection.count()

    def count(self) -> int:
        return self._collection().count()
