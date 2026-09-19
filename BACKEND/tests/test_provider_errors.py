"""Diagnóstico público restrito e leitura segura do Retry-After, sem rede."""

from datetime import datetime, timezone

import httpx
import pytest

from app.services.llm.provider_errors import diagnose_provider_error, parse_retry_after


@pytest.mark.parametrize(("value", "expected"), [
    (None, None), ("", None), (" 7 ", 7), ("0", 0), ("-1", None),
    ("1.5", None), ("NaN", None), ("inf", None), ("inválido", None),
    ("９", None), ("9" * 5000, 2_147_483_647),
    ("Sat, 19 Sep 2026 12:00:05 GMT", 5),
    ("Sat, 19 Sep 2026 11:59:00 GMT", 0),
    ("Sat, 19 Sep 2026 12:00:05", None),
])
def test_retry_after_formats(value, expected):
    assert parse_retry_after(value, now=datetime(2026, 9, 19, 12, tzinfo=timezone.utc)) == expected


def test_http_date_rounds_up_instead_of_retrying_early():
    now = datetime(2026, 9, 19, 12, 0, 0, 900_000, tzinfo=timezone.utc)
    assert parse_retry_after("Sat, 19 Sep 2026 12:00:05 GMT", now=now) == 5


@pytest.mark.parametrize("payload", [None, [], "secret", {"error": []}, {"error": {"metadata": []}}])
def test_malformed_error_body_still_produces_safe_unknown_origin(payload):
    response = httpx.Response(429, json=payload)
    diagnostic = diagnose_provider_error(response)
    assert diagnostic.source == "unknown" and diagnostic.reason == "rate_limit"
    assert diagnostic.retry_after_seconds is None


def test_html_body_is_not_exposed():
    diagnostic = diagnose_provider_error(httpx.Response(429, text="<html>segredo</html>"))
    assert diagnostic.http_status == 429 and diagnostic.source == "unknown"
    assert "segredo" not in diagnostic.model_dump_json()


def test_platform_headers_identify_openrouter_without_copying_values():
    diagnostic = diagnose_provider_error(httpx.Response(429, headers={
        "X-RateLimit-Limit": "segredo", "Retry-After": "10",
    }))
    assert diagnostic.source == "openrouter" and diagnostic.retry_after_seconds == 10
    assert "segredo" not in diagnostic.model_dump_json()


@pytest.mark.parametrize(("metadata", "expected_source", "expected_reason"), [
    ({"provider_name": "Mistral", "provider_code": "capacity_exceeded"}, "provider", "capacity"),
    ({"provider_code": "insufficient_quota"}, "provider", "quota"),
    ({"provider_code": 429}, "provider", "rate_limit"),
    ({"provider_code": {"secret": "hidden"}}, "provider", "rate_limit"),
    ({"error_type": "rate_limit_exceeded"}, "unknown", "rate_limit"),
    ({"limit_source": []}, "unknown", "rate_limit"),
])
def test_categorizes_only_known_metadata_values(metadata, expected_source, expected_reason):
    diagnostic = diagnose_provider_error(httpx.Response(429, json={"error": {"metadata": metadata}}))
    assert (diagnostic.source, diagnostic.reason) == (expected_source, expected_reason)


@pytest.mark.parametrize(("metadata", "reason"), [
    ({"limit_source": "openrouter_key_limit"}, "key_credit_limit"),
    ({"limit_source": "openrouter_in_flight_budget"}, "in_flight_budget"),
    ({"limit_source": "openrouter_credits"}, "credits"),
    ({"limit_source": "openrouter_credits", "reason": "weight_exceeds_budget"}, "request_budget"),
])
def test_credit_limits_are_not_confused_with_request_limits(metadata, reason):
    diagnostic = diagnose_provider_error(httpx.Response(402, json={"error": {"metadata": metadata}}))
    assert (diagnostic.source, diagnostic.reason) == ("openrouter", reason)
