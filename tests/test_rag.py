from rag.cache import TTLCache
from rag.indexer import chunk_text
from rag.models import Evidence, SearchResult
from rag.indexer import MedicalIndexer
from rag.service import RetrievalService


def test_chunk_text_keeps_content_and_splits():
    text = "第一句话。" * 100
    chunks = chunk_text(text, chunk_size=80, overlap=10)
    assert len(chunks) > 1
    assert all(chunks)


def test_ttl_cache():
    cache = TTLCache(ttl_seconds=60, max_size=2)
    cache.set("a", 1)
    assert cache.get("a") == 1
    cache.clear()
    assert cache.get("a") is None


class FakeRetrievalService:
    def search(self, query, top_k=5, **kwargs):
        return SearchResult(query, [Evidence("1", "指南", "标题", "证据内容", .9)], 1.0, False, "fake-bge")


def test_fake_result_shape():
    result = FakeRetrievalService().search("测试")
    assert result.evidences[0].to_dict()["relevance"] == .9


class FakeEmbedder:
    model_name = "fake-bge"

    @staticmethod
    def _vector(text):
        return [float(text.count("头痛") + 1), float(text.count("用药") + 1), float(len(text) % 17 + 1)]

    def encode_documents(self, texts):
        return [self._vector(text) for text in texts]

    def encode_query(self, query):
        return self._vector(query)


def test_chroma_vector_database_roundtrip(tmp_path):
    documents = [
        {"id": "headache", "title": "头痛指南", "source": "测试指南", "content": "头痛伴危险信号需要就医。"},
        {"id": "medicine", "title": "用药指南", "source": "测试药典", "content": "用药前应核对过敏史。"},
    ]
    indexer = MedicalIndexer(FakeEmbedder(), tmp_path / "chroma")
    assert indexer.build(documents) == 2
    service = RetrievalService(FakeEmbedder(), tmp_path / "chroma")
    result = service.search("头痛危险信号", top_k=1)
    assert len(result.evidences) == 1
    assert result.model == "fake-bge"
