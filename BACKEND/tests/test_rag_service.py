"""Testes da recuperação, prompt e política de ausência de contexto."""

import asyncio
from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_service
from app.core.config import Settings
from app.main import app
from app.models.chat import ChatHistoryMessage, ChatRequest
from app.services.documents import DocumentProcessor, DocumentService
from app.services.rag import ChatService, RetrievalService
from tests.fakes import FakeEmbeddingService, FakeLLMClient, InMemoryVectorStore


def build_services(**settings_overrides: object) -> tuple[DocumentService, RetrievalService]:
    settings = Settings(
        _env_file=None,
        retrieval_min_relevance=0.99,
        **settings_overrides,
    )
    embeddings = FakeEmbeddingService()
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
    return documents, retrieval


def test_retrieves_a_known_chunk_with_source_metadata() -> None:
    documents, retrieval = build_services()
    content = "A Aurora Tech oferece consultoria em transformação digital."
    indexed = documents.index_document(
        filename="servicos.txt",
        content=content.encode(),
        content_type="text/plain",
    )

    chunks = retrieval.retrieve(content)

    assert len(chunks) == 1
    assert chunks[0].document_id == indexed.id
    assert chunks[0].document_name == "servicos.txt"
    assert chunks[0].relevance > 0.99


def test_prompt_contains_context_history_and_question_without_secret() -> None:
    documents, retrieval = build_services()
    content = "A Aurora Tech atende pequenas e médias empresas."
    documents.index_document(
        filename="empresa.md",
        content=content.encode(),
        content_type="text/markdown",
    )
    llm = FakeLLMClient()
    service = ChatService(retrieval_service=retrieval, llm_client=llm)
    request = ChatRequest(
        message=content,
        history=[ChatHistoryMessage(role="user", content="Quem é a empresa?")],
    )

    response = asyncio.run(service.answer(request))

    assert response.has_context is True
    assert response.sources[0].document_name == "empresa.md"
    assert len(llm.calls) == 1
    prompt = "\n".join(message["content"] for message in llm.calls[0])
    assert content in prompt
    assert "Quem é a empresa?" in prompt
    assert request.message in prompt
    assert "OPENROUTER_API_KEY" not in prompt
    assert "Bearer" not in prompt


def test_does_not_call_model_when_collection_has_no_context() -> None:
    _, retrieval = build_services()
    llm = FakeLLMClient()
    service = ChatService(retrieval_service=retrieval, llm_client=llm)

    response = asyncio.run(
        service.answer(ChatRequest(message="Qual é a política de viagens?"))
    )

    assert response.has_context is False
    assert response.sources == []
    assert "Não encontrei" in response.answer
    assert llm.calls == []


def test_context_respects_configured_character_limit() -> None:
    documents, retrieval = build_services(
        max_context_characters=500,
        chunk_size=200,
        chunk_overlap=20,
    )
    content = ("Aurora Tech transformação digital. " * 40).strip()
    documents.index_document(
        filename="longo.txt",
        content=content.encode(),
        content_type="text/plain",
    )

    chunks = retrieval.retrieve(content[:200])

    assert sum(len(chunk.content) for chunk in chunks) <= 500


def test_chat_endpoint_uses_retrieval_and_simulated_openrouter() -> None:
    documents, retrieval = build_services()
    content = "O suporte da Aurora Tech funciona em horário comercial."
    documents.index_document(
        filename="suporte.txt",
        content=content.encode(),
        content_type="text/plain",
    )
    llm = FakeLLMClient("O suporte funciona em horário comercial.")
    service = ChatService(retrieval_service=retrieval, llm_client=llm)
    app.dependency_overrides[get_chat_service] = lambda: service

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/chat",
                json={"message": content, "history": []},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["answer"] == "O suporte funciona em horário comercial."
    assert response.json()["has_context"] is True
    assert response.json()["sources"][0]["document_name"] == "suporte.txt"
