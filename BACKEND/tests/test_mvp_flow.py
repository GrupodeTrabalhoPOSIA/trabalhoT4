"""Validação integrada dos fluxos essenciais do MVP."""

import math
import unicodedata
from io import BytesIO
import pymupdf
from docx import Document
from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_service, get_document_service
from app.core.config import Settings
from app.main import app
from app.services.documents import DocumentProcessor, DocumentService
from app.services.rag import ChatService, RetrievalService
from tests.fakes import FakeLLMClient, InMemoryVectorStore


class TopicEmbeddingService:
    """Separa assuntos para tornar o teste integrado determinístico."""

    topics = ("servico", "missao", "suporte", "seguranca")

    @classmethod
    def _embed(cls, text: str) -> list[float]:
        normalized = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
        vector = [float(topic in normalized) for topic in cls.topics]
        if not any(vector):
            vector.append(1.0)
        else:
            vector.append(0.0)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def make_pdf(text: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def make_docx(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_complete_document_chat_persistence_and_removal_flow() -> None:
    settings = Settings(
        _env_file=None,
        retrieval_min_relevance=0.8,
    )
    embeddings = TopicEmbeddingService()
    store = InMemoryVectorStore()
    documents = DocumentService(
        processor=DocumentProcessor(settings),
        embedding_service=embeddings,
        vector_store=store,
    )
    retrieval = RetrievalService(
        settings=settings,
        embedding_service=embeddings,
        vector_store=store,
    )
    llm = FakeLLMClient("A Aurora Tech oferece desenvolvimento de sistemas.")
    chat = ChatService(retrieval_service=retrieval, llm_client=llm)
    app.dependency_overrides[get_document_service] = lambda: documents
    app.dependency_overrides[get_chat_service] = lambda: chat

    files = [
        ("servicos.txt", b"Servicos de desenvolvimento de sistemas.", "text/plain"),
        ("missao.md", b"# Missao\nTornar a inovacao acessivel.", "text/markdown"),
        ("suporte.pdf", make_pdf("Suporte em horario comercial."), "application/pdf"),
        (
            "seguranca.docx",
            make_docx("Seguranca e privacidade de dados."),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
    ]

    try:
        with TestClient(app) as client:
            uploads = [
                client.post("/api/v1/documents", files={"file": file}) for file in files
            ]
            assert all(response.status_code == 201 for response in uploads)
            assert len(client.get("/api/v1/documents").json()) == 4

            answer = client.post(
                "/api/v1/chat",
                json={"message": "Quais servicos são oferecidos?", "history": []},
            )
            assert answer.status_code == 200
            assert answer.json()["has_context"] is True
            assert answer.json()["sources"][0]["document_name"] == "servicos.txt"

            refusal = client.post(
                "/api/v1/chat",
                json={"message": "Qual a previsão do tempo em Marte?", "history": []},
            )
            assert refusal.status_code == 200
            assert refusal.json()["has_context"] is False
            assert refusal.json()["sources"] == []

            service_id = uploads[0].json()["id"]
            assert client.delete(f"/api/v1/documents/{service_id}").status_code == 204
            after_removal = client.post(
                "/api/v1/chat",
                json={"message": "Quais servicos são oferecidos?", "history": []},
            )
            assert after_removal.json()["has_context"] is False

        assert len(store.list_documents()) == 3
    finally:
        app.dependency_overrides.clear()
