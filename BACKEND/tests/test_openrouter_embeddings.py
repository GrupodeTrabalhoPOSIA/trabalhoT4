"""Testes do cliente de embeddings OpenRouter sem chamadas externas."""

import json

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.errors import AppError
from app.services.embeddings.openrouter import OpenRouterEmbeddingService


def make_settings(**overrides: object) -> Settings:
    overrides.setdefault("openrouter_embedding_model", "openai/text-embedding-3-small")
    return Settings(
        _env_file=None,
        openrouter_api_key=SecretStr("segredo-de-teste"),
        embedding_dimensions=3,
        **overrides,
    )


def test_sends_batched_payload_and_restores_response_order() -> None:
    captured: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        captured.append(
            {
                "authorization": request.headers["Authorization"],
                "referer": request.headers["HTTP-Referer"],
                "payload": payload,
            }
        )
        if len(captured) == 1:
            return httpx.Response(
                200,
                json={
                    "data": [
                        {"index": 1, "embedding": [0, 1, 0]},
                        {"index": 0, "embedding": [1, 0, 0]},
                    ]
                },
            )
        return httpx.Response(
            200,
            json={"data": [{"index": 0, "embedding": [0, 0, 1]}]},
        )

    service = OpenRouterEmbeddingService(
        make_settings(
            openrouter_embedding_model="openai/modelo-de-teste",
            embedding_batch_size=2,
        ),
        transport=httpx.MockTransport(handler),
    )

    vectors = service.embed_documents(["primeiro", "segundo", "terceiro"])

    assert vectors == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    assert len(captured) == 2
    assert captured[0]["authorization"] == "Bearer segredo-de-teste"
    assert captured[0]["referer"] == "http://localhost:5173"
    assert captured[0]["payload"] == {
        "model": "openai/modelo-de-teste",
        "input": ["primeiro", "segundo"],
        "dimensions": 3,
    }
    assert captured[1]["payload"] == {
        "model": "openai/modelo-de-teste",
        "input": ["terceiro"],
        "dimensions": 3,
    }


def test_embed_query_returns_the_single_vector() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={"data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}]},
        )
    )
    service = OpenRouterEmbeddingService(make_settings(), transport=transport)

    assert service.embed_query("consulta") == [0.1, 0.2, 0.3]


def test_mistral_uses_fixed_dimensions_for_documents_and_queries() -> None:
    inputs = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["model"] == "mistralai/mistral-embed-2312"
        assert "dimensions" not in payload
        inputs.append(payload["input"])
        return httpx.Response(200, json={"data": [
            {"index": i, "embedding": [0.1] * 1024}
            for i in range(len(payload["input"]))
        ]})

    service = OpenRouterEmbeddingService(
        Settings(_env_file=None, openrouter_api_key="chave-de-teste"),
        transport=httpx.MockTransport(handler),
    )
    assert len(service.embed_documents(["trecho"])[0]) == 1024
    assert len(service.embed_query("pergunta")) == 1024
    assert inputs == [["trecho"], ["pergunta"]]


def test_empty_document_batch_does_not_require_configuration() -> None:
    settings = Settings(_env_file=None, openrouter_api_key=None)

    assert OpenRouterEmbeddingService(settings).embed_documents([]) == []


def test_mistral_rejects_vectors_with_the_old_dimension() -> None:
    service = OpenRouterEmbeddingService(
        Settings(_env_file=None, openrouter_api_key="chave-de-teste"),
        transport=httpx.MockTransport(lambda _: httpx.Response(
            200, json={"data": [{"index": 0, "embedding": [0.1] * 384}]}
        )),
    )
    with pytest.raises(AppError) as captured:
        service.embed_query("consulta")
    assert captured.value.code == "EMBEDDINGS_INVALID_RESPONSE"


def test_missing_key_returns_safe_configuration_error() -> None:
    settings = Settings(_env_file=None, openrouter_api_key=None)

    with pytest.raises(AppError) as captured:
        OpenRouterEmbeddingService(settings).embed_query("consulta")

    assert captured.value.status_code == 503
    assert captured.value.code == "EMBEDDINGS_NOT_CONFIGURED"


@pytest.mark.parametrize(
    ("provider_status", "expected_code"),
    [
        (401, "EMBEDDINGS_AUTH_ERROR"),
        (429, "EMBEDDINGS_RATE_LIMITED"),
        (404, "EMBEDDINGS_UNAVAILABLE"),
        (500, "EMBEDDINGS_PROVIDER_ERROR"),
    ],
)
def test_maps_provider_errors(provider_status: int, expected_code: str) -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            provider_status,
            json={"error": {"message": "segredo privado"}},
        )
    )
    service = OpenRouterEmbeddingService(make_settings(), transport=transport)

    with pytest.raises(AppError) as captured:
        service.embed_query("consulta")

    assert captured.value.code == expected_code
    assert "segredo privado" not in captured.value.message


def test_timeout_is_mapped_without_exposing_provider_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("tempo excedido com segredo", request=request)

    service = OpenRouterEmbeddingService(
        make_settings(),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AppError) as captured:
        service.embed_query("consulta")

    assert captured.value.status_code == 504
    assert captured.value.code == "EMBEDDINGS_TIMEOUT"
    assert "segredo" not in captured.value.message


@pytest.mark.parametrize(
    "response_data",
    [
        {"data": []},
        {"data": [{"index": 1, "embedding": [0.1, 0.2, 0.3]}]},
        {"data": [{"index": 0, "embedding": [0.1, 0.2]}]},
        b'{"data":[{"index":0,"embedding":[0.1,NaN,0.3]}]}',
    ],
)
def test_rejects_malformed_success_response(response_data: object) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        if isinstance(response_data, bytes):
            return httpx.Response(200, content=response_data)
        return httpx.Response(200, json=response_data)

    service = OpenRouterEmbeddingService(
        make_settings(),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AppError) as captured:
        service.embed_query("consulta")

    assert captured.value.status_code == 502
    assert captured.value.code == "EMBEDDINGS_INVALID_RESPONSE"
