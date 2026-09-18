"""Configuração de logs operacionais sem conteúdo de mensagens ou credenciais."""

import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import FastAPI, Request, Response

logger = logging.getLogger("aurora.api")


def configure_logging(level: str) -> None:
    """Configura um formato pequeno e previsível para execução acadêmica."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def register_request_logging(application: FastAPI) -> None:
    """Registra somente metadados da requisição, nunca corpo ou cabeçalhos."""

    @application.middleware("http")
    async def log_request(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started_at = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - started_at) * 1000
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
