"""Testes integrados dos endpoints e da persistência vetorial."""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_document_service
from app.core.config import Settings
from app.main import app
from app.services.documents import DocumentProcessor, DocumentService
from tests.fakes import FakeEmbeddingService, InMemoryVectorStore


def make_service(store: InMemoryVectorStore | None = None) -> DocumentService:
    settings = Settings(_env_file=None)
    return DocumentService(
        processor=DocumentProcessor(settings),
        embedding_service=FakeEmbeddingService(),
        vector_store=store or InMemoryVectorStore(),
    )


@pytest.fixture
def client() -> TestClient:
    service = make_service()
    app.dependency_overrides[get_document_service] = lambda: service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_document_lifecycle(client: TestClient) -> None:
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("aurora.txt", b"Aurora Tech oferece solucoes digitais.", "text/plain")},
    )

    assert upload.status_code == 201
    document = upload.json()
    assert document["name"] == "aurora.txt"
    assert document["chunk_count"] == 1

    listed = client.get("/api/v1/documents")
    assert listed.status_code == 200
    assert listed.json() == [document]

    content = client.get(f"/api/v1/documents/{document['id']}/content")
    assert content.status_code == 200
    assert content.json() == {
        "id": document["id"],
        "chunks": [{
            "content": "Aurora Tech oferece solucoes digitais.",
            "chunk_index": 0,
            "page": None,
        }],
    }

    duplicate = client.post(
        "/api/v1/documents",
        files={"file": ("copia.txt", b"Aurora Tech oferece solucoes digitais.", "text/plain")},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "DUPLICATE_DOCUMENT"

    deleted = client.delete(f"/api/v1/documents/{document['id']}")
    assert deleted.status_code == 204
    assert client.get("/api/v1/documents").json() == []
    assert client.get(f"/api/v1/documents/{document['id']}/content").status_code == 404


def test_delete_unknown_document_returns_404(client: TestClient) -> None:
    response = client.delete("/api/v1/documents/inexistente")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DOCUMENT_NOT_FOUND"


def test_vectors_remain_available_through_shared_store() -> None:
    store = InMemoryVectorStore()
    service = make_service(store)
    indexed = service.index_document(
        filename="aurora.md",
        content=b"# Aurora Tech\n\nConhecimento persistente.",
        content_type="text/markdown",
    )

    another_service_instance = make_service(store)
    documents = another_service_instance.list_documents()

    assert len(documents) == 1
    assert documents[0].id == indexed.id
    assert len(store.chunks) == indexed.chunk_count
    content = another_service_instance.get_document_content(indexed.id)
    assert content.chunks[0].content == "# Aurora Tech\n\nConhecimento persistente."


def test_content_rejects_invalid_document_id(client: TestClient) -> None:
    assert client.get("/api/v1/documents/invalid/content").status_code == 422


def test_content_returns_ordered_chunks_for_only_requested_document(client: TestClient) -> None:
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("longo.txt", ("Aurora Tech. " * 180).encode(), "text/plain")},
    )
    other = client.post(
        "/api/v1/documents",
        files={"file": ("outro.txt", b"Outro documento separado.", "text/plain")},
    )
    assert other.status_code == 201
    document = upload.json()
    chunks = client.get(f"/api/v1/documents/{document['id']}/content").json()["chunks"]
    assert len(chunks) == document["chunk_count"] > 1
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    assert all("Outro documento" not in chunk["content"] for chunk in chunks)
