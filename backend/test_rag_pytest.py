# Tests use pytest + pytest-asyncio (no other framework detected in repo).
# To run:  pytest -q backend

import pytest
import asyncio
from pytest import mark
from app.services.rag_service import DocumentChunker, VectorRetriever, RAGService

pytestmark = mark.asyncio

@pytest.fixture
def sample_document_text():
    return """이것은 샘플 문서입니다.
이 문서는 테스트를 위해 작성되었습니다.
여러 줄로 이루어진 문서의 청크를 생성합니다.
"""

@pytest.fixture
def sample_chunks():
    return [
        {"text": "이것은 샘플 문서의 첫 번째 청크입니다. 여기에는 일부 텍스트가 포함됩니다.", "document_id": "doc1"},
        {"text": "문서의 두 번째 청크입니다. 이전 청크와 일부 오버랩이 있습니다.", "document_id": "doc1"},
        {"text": "마지막 세 번째 청크입니다. 테스트를 위한 마지막 부분입니다.", "document_id": "doc1"},
    ]

@pytest.fixture(autouse=True)
def stub_embedding(monkeypatch):
    async def fake_embed(self, texts):
        # Return deterministic small-dim vectors based on hash
        return [[hash(t) % 1000 / 1000] for t in texts]
    monkeypatch.setattr(VectorRetriever, "_embed_async", fake_embed, raising=False)

@pytest.fixture
async def vector_retriever():
    vr = VectorRetriever()
    try:
        yield vr
    finally:
        # best-effort cleanup so independent tests start with empty store
        try:
            await vr._reset_store_for_test()
        except AttributeError:
            # cleanup helper not available, relying on GC
            pass

async def test_chunk_document_basic(sample_document_text):
    chunker = DocumentChunker(chunk_size=200, chunk_overlap=20)
    chunks = chunker.chunk_document(sample_document_text, "doc1")
    assert chunks and isinstance(chunks, list)
    assert all("text" in c and "document_id" in c and c["document_id"] == "doc1" for c in chunks)
    # Ensure overlap strings appear in consecutive chunks
    for prev, nxt in zip(chunks, chunks[1:]):
        assert prev["text"][-20:] in nxt["text"]

async def test_chunk_document_empty():
    chunker = DocumentChunker(chunk_size=100)
    chunks = chunker.chunk_document("", "empty")
    assert chunks == []

async def test_vector_retriever_add_invalid(vector_retriever):
    with pytest.raises(ValueError):
        await vector_retriever.add_documents_to_store("proj", [])

async def test_vector_retriever_search_happy(vector_retriever, sample_chunks):
    ok = await vector_retriever.add_documents_to_store("proj", sample_chunks)
    assert ok
    res = await vector_retriever.search_similar_documents("proj", "FastAPI", k=2)
    assert len(res) == 2
    assert res[0]["similarity"] >= res[1]["similarity"]

async def test_rag_service_search_integration(monkeypatch):
    async def fake_search(self, project, query, k):
        return [{"content": "stub result", "similarity": 0.99}]
    monkeypatch.setattr(VectorRetriever, "search_similar_documents", fake_search)
    rag = RAGService()
    res = await rag.search_documents("proj", "whatever", max_results=1)
    assert res == [{"content": "stub result", "similarity": 0.99}]

async def test_rag_service_search_failure(monkeypatch):
    async def fake_search_fail(self, project, query, k):
        raise RuntimeError("Search service failure")
    monkeypatch.setattr(VectorRetriever, "search_similar_documents", fake_search_fail)
    rag = RAGService()
    with pytest.raises(RuntimeError):
        await rag.search_documents("proj", "error", max_results=1)

# EOF