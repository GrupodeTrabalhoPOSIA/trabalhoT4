"""Testes de robustez dos erros e dos logs públicos."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_service
from app.main import app
from app.core.errors import AppError
from app.models.errors import ProviderDiagnostic


class ExplodingChatService:
    async def answer(self, _: object) -> object:
        raise RuntimeError("OPENROUTER_API_KEY=segredo-que-nao-pode-aparecer")


def test_unexpected_error_is_standardized_without_logging_secret(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app.dependency_overrides[get_chat_service] = lambda: ExplodingChatService()
    try:
        with caplog.at_level(logging.ERROR):
            with TestClient(app, raise_server_exceptions=False) as client:
                response = client.post(
                    "/api/v1/chat",
                    json={"message": "Pergunta válida", "history": []},
                )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "code": "INTERNAL_ERROR",
            "message": "Ocorreu um erro interno inesperado.",
        }
    }
    assert "segredo-que-nao-pode-aparecer" not in caplog.text
    assert "RuntimeError" in caplog.text


def test_model_diagnostic_is_included_in_standard_error_envelope():
    class RateLimitedChatService:
        async def answer(self, _):
            raise AppError(status_code=502, code="MODEL_RATE_LIMITED", message="Limite de requisições.",
                           diagnostic=ProviderDiagnostic(http_status=429, reason="rate_limit", retry_after_seconds=5))

    app.dependency_overrides[get_chat_service] = lambda: RateLimitedChatService()
    try:
        response = TestClient(app).post("/api/v1/chat", json={"message": "Pergunta válida", "history": []})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 502
    diagnostic = response.json()["detail"]["details"]["provider"]
    assert diagnostic["http_status"] == 429 and diagnostic["source"] == "unknown"
    assert diagnostic["retry_after_seconds"] == 5
