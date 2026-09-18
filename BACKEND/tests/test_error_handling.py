"""Testes de robustez dos erros e dos logs públicos."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_service
from app.main import app


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
