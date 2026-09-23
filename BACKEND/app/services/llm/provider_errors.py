"""Diagnóstico de erros HTTP sem publicar corpos, mensagens livres ou credenciais."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from math import ceil

import httpx

from app.models.errors import ProviderDiagnostic


def normalize_provider_response(response: httpx.Response) -> httpx.Response:
    """Erros após o início da geração podem vir dentro de HTTP 200."""
    if response.status_code >= 400:
        return response
    try:
        payload = response.json()
    except ValueError:
        return response
    if not isinstance(payload, dict) or "error" not in payload:
        return response
    error = payload["error"]
    code = error.get("code") if isinstance(error, dict) else None
    if isinstance(code, str) and code.isascii() and code.isdecimal() and len(code) == 3:
        code = int(code)
    if type(code) is not int or not 400 <= code <= 599:
        code = 502
    return httpx.Response(code, headers=response.headers, content=response.content)


def parse_retry_after(value: str | None, *, now: datetime | None = None) -> int | None:
    """Aceita delta em segundos ou HTTP-date; arredonda para nunca antecipar o retry."""
    if value is None:
        return None
    value = value.strip()
    if value.isascii() and value.isdecimal():
        # Saturação evita inteiros gigantes. Continua acima do teto de retry do fluxo.
        return min(int(value), 2_147_483_647) if len(value) <= 10 else 2_147_483_647
    try:
        deadline = parsedate_to_datetime(value)
        if deadline.tzinfo is None:
            return None
        return max(0, ceil((deadline - (now or datetime.now(timezone.utc))).total_seconds()))
    except (TypeError, ValueError, OverflowError):
        return None


def diagnose_provider_error(response: httpx.Response) -> ProviderDiagnostic:
    try:
        payload = response.json()
    except ValueError:
        payload = None
    error = payload.get("error") if isinstance(payload, dict) else None
    metadata = error.get("metadata") if isinstance(error, dict) else None
    metadata = metadata if isinstance(metadata, dict) else {}

    # Valores arbitrários (inclusive metadata.raw e error.message) não são copiados.
    source = "unknown"
    reason = "rate_limit" if response.status_code == 429 else "credits" if response.status_code == 402 else "unknown"
    limit_source = metadata.get("limit_source")
    credit_sources = {
        "openrouter_credits": "credits",
        "openrouter_key_limit": "key_credit_limit",
        "openrouter_in_flight_budget": "in_flight_budget",
    }
    if isinstance(limit_source, str) and limit_source in credit_sources:
        source, reason = "openrouter", credit_sources[limit_source]
        if metadata.get("reason") == "weight_exceeds_budget":
            reason = "request_budget"
    elif metadata.get("provider_name") or metadata.get("provider_code") is not None:
        source = "provider"
    elif any(name in response.headers for name in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset")):
        source = "openrouter"

    if response.status_code == 429:
        known_reasons = {
            "capacity_exceeded": "capacity", "overloaded": "capacity",
            "insufficient_quota": "quota", "quota_exceeded": "quota",
        }
        for value in (metadata.get("provider_code"), metadata.get("error_type"), metadata.get("reason")):
            if isinstance(value, str) and value.lower() in known_reasons:
                reason = known_reasons[value.lower()]
                break

    return ProviderDiagnostic(
        http_status=response.status_code,
        source=source,
        reason=reason,
        retry_after_seconds=parse_retry_after(response.headers.get("Retry-After")),
    )
