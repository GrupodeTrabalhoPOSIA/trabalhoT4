"""Testes do contrato HTTP do chat."""

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_service
from app.main import app
from app.models.chat import ChatResponse


class StubChatService:
    async def answer(self, _: object) -> ChatResponse:
        return ChatResponse(
            answer="Resposta de teste.",
            sources=[],
            has_context=True,
        )


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[get_chat_service] = lambda: StubChatService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_chat_rejects_blank_message_with_standard_error(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"message": "   ", "history": []})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_chat_rejects_message_above_limit(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"message": "a" * 2001, "history": []})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_chat_rejects_history_above_limit(client: TestClient) -> None:
    history = [{"role": "user", "content": f"Mensagem {index}"} for index in range(11)]

    response = client.post("/api/v1/chat", json={"message": "Pergunta", "history": history})

    assert response.status_code == 422


def test_valid_chat_request_returns_typed_response(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"message": "Pergunta", "history": []})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Resposta de teste.",
        "sources": [],
        "has_context": True,
    }


def test_chat_contract_is_available_in_openapi(client: TestClient) -> None:
    openapi = client.get("/openapi.json").json()

    assert "/api/v1/chat" in openapi["paths"]
    assert "ChatRequest" in openapi["components"]["schemas"]
    assert "ChatResponse" in openapi["components"]["schemas"]
