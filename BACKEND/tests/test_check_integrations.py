"""O diagnóstico deve ser opt-in, sem rede por padrão e sem segredos na saída."""

import asyncio
import json

import httpx

from app.check_integrations import check
from app.core.config import Settings


def test_configuration_check_does_not_connect_or_expose_key(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Não deve acessar rede")

    monkeypatch.setattr(httpx, "AsyncClient", forbidden)
    report = asyncio.run(check(Settings(_env_file=None, openrouter_api_key="private-key")))
    assert report["openrouter_key_configured"] is True
    assert report["remote_checks"] == "not_requested"
    assert "private-key" not in json.dumps(report)


def test_live_check_stops_on_invalid_key_without_chat(monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(401, json={"error": {"message": "private-provider-message"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: client)
    report = asyncio.run(check(Settings(_env_file=None, openrouter_api_key="private-key"), live=True))
    assert report["key_http_status"] == 401
    assert report["remote_checks"] == "key_check_failed"
    assert len(calls) == 1 and calls[0].method == "GET"
    assert "private" not in json.dumps(report)


def test_live_check_reports_missing_key():
    report = asyncio.run(check(Settings(_env_file=None, openrouter_api_key=None), live=True))
    assert report["remote_checks"] == "MODEL_NOT_CONFIGURED"
