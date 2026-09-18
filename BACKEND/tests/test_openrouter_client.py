"""Testes do contrato HTTP do cliente OpenRouter sem chamadas externas."""

import asyncio

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.errors import AppError
from app.services.llm.openrouter import OpenRouterClient


def test_sends_expected_payload_and_headers() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["authorization"] = request.headers["Authorization"]
        captured["referer"] = request.headers["HTTP-Referer"]
        captured["body"] = request.content
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": " Resposta segura. "}}]},
        )

    settings = Settings(
        _env_file=None,
        openrouter_api_key=SecretStr("segredo-de-teste"),
        openrouter_model="modelo/teste",
    )
    client = OpenRouterClient(settings, transport=httpx.MockTransport(handler))

    answer = asyncio.run(
        client.complete([{"role": "user", "content": "Olá"}])
    )

    assert answer == "Resposta segura."
    assert captured["authorization"] == "Bearer segredo-de-teste"
    assert captured["referer"] == "http://localhost:5173"
    body = bytes(captured["body"]).decode()
    assert '"model":"modelo/teste"' in body


@pytest.mark.parametrize(
    ("provider_status", "expected_code"),
    [(401, "MODEL_AUTH_ERROR"), (429, "MODEL_RATE_LIMITED"), (404, "MODEL_UNAVAILABLE")],
)
def test_maps_provider_errors(provider_status: int, expected_code: str) -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(provider_status, json={"error": {"message": "privado"}})
    )
    settings = Settings(
        _env_file=None,
        openrouter_api_key=SecretStr("segredo-de-teste"),
    )

    with pytest.raises(AppError) as captured:
        asyncio.run(
            OpenRouterClient(settings, transport=transport).complete(
                [{"role": "user", "content": "Olá"}]
            )
        )

    assert captured.value.code == expected_code
    assert "privado" not in captured.value.message


def test_missing_key_returns_safe_configuration_error() -> None:
    settings = Settings(_env_file=None, openrouter_api_key=None)

    with pytest.raises(AppError) as captured:
        asyncio.run(
            OpenRouterClient(settings).complete(
                [{"role": "user", "content": "Olá"}]
            )
        )

    assert captured.value.status_code == 503
    assert captured.value.code == "MODEL_NOT_CONFIGURED"


def test_timeout_is_mapped_to_gateway_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("tempo excedido com dado privado", request=request)

    settings = Settings(
        _env_file=None,
        openrouter_api_key=SecretStr("segredo-de-teste"),
    )

    with pytest.raises(AppError) as captured:
        asyncio.run(
            OpenRouterClient(settings, transport=httpx.MockTransport(handler)).complete(
                [{"role": "user", "content": "Olá"}]
            )
        )

    assert captured.value.status_code == 504
    assert captured.value.code == "MODEL_TIMEOUT"
    assert "privado" not in captured.value.message


def test_malformed_success_response_is_rejected() -> None:
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"choices": []}))
    settings = Settings(
        _env_file=None,
        openrouter_api_key=SecretStr("segredo-de-teste"),
    )

    with pytest.raises(AppError) as captured:
        asyncio.run(
            OpenRouterClient(settings, transport=transport).complete(
                [{"role": "user", "content": "Olá"}]
            )
        )

    assert captured.value.code == "MODEL_INVALID_RESPONSE"
