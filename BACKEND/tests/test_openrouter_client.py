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
        openrouter_model="mistralai/mistral-large",
    )
    client = OpenRouterClient(settings, transport=httpx.MockTransport(handler))

    answer = asyncio.run(
        client.complete([{"role": "user", "content": "Olá"}])
    )

    assert answer == "Resposta segura."
    assert captured["authorization"] == "Bearer segredo-de-teste"
    assert captured["referer"] == "http://localhost:5173"
    body = bytes(captured["body"]).decode()
    assert '"model":"mistralai/mistral-large"' in body


def test_legacy_gpt_environment_still_sends_only_mistral(monkeypatch) -> None:
    import json

    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "Teste."}}]})

    settings = Settings(_env_file=None, openrouter_api_key=SecretStr("segredo-de-teste"))
    asyncio.run(OpenRouterClient(settings, transport=httpx.MockTransport(handler)).complete(
        [{"role": "user", "content": "Olá"}]
    ))
    assert captured[0]["model"] == "mistralai/mistral-large"
    assert "models" not in captured[0]  # Sem fallback para outro modelo.


@pytest.mark.parametrize(
    ("provider_status", "expected_code"),
    [(401, "MODEL_AUTH_ERROR"), (403, "MODEL_AUTH_ERROR"), (429, "MODEL_RATE_LIMITED"), (402, "MODEL_CREDIT_LIMIT"), (404, "MODEL_UNAVAILABLE")],
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


def test_error_diagnostics_and_logs_never_expose_free_text_or_secrets(caplog) -> None:
    secret = "sk-or-v1-secret-test"
    private_text = f"Bearer {secret}; pessoa@example.com; pergunta privada"
    response = httpx.Response(429, headers={"Retry-After": "3", "X-Private": private_text}, json={
        "error": {"message": private_text, "metadata": {
            "provider_name": private_text, "provider_code": "capacity_exceeded",
            "raw": private_text, "remedy_hint": private_text,
        }},
    })
    settings = Settings(_env_file=None, openrouter_api_key=SecretStr(secret))
    calls = []

    def handler(request):
        calls.append(request)
        return response

    with pytest.raises(AppError) as captured:
        asyncio.run(OpenRouterClient(settings, transport=httpx.MockTransport(handler)).complete(
            [{"role": "user", "content": "pergunta privada"}],
        ))
    diagnostic = captured.value.diagnostic
    assert diagnostic.source == "provider" and diagnostic.reason == "capacity"
    assert diagnostic.retry_after_seconds == 3
    assert len(calls) == 1  # Retry pertence ao fluxo, nunca ao cliente HTTP.
    public_data = f"{captured.value} {diagnostic.model_dump_json()} {caplog.text}"
    for forbidden in (secret, "pessoa@example.com", "pergunta privada", "Bearer"):
        assert forbidden not in public_data
    assert "model_provider_error" in caplog.text and "429" in caplog.text
