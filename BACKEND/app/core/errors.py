"""Erros de aplicação e handlers HTTP padronizados."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.models.errors import ErrorDetail, ErrorResponse

logger = logging.getLogger("aurora.errors")


class AppError(Exception):
    """Erro conhecido que pode ser apresentado ao consumidor da API."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def register_exception_handlers(application: FastAPI) -> None:
    """Registra respostas consistentes para erros conhecidos e de validação."""

    @application.exception_handler(AppError)
    async def handle_app_error(request: Request, exception: AppError) -> JSONResponse:
        logger.warning(
            "application_error path=%s status=%s code=%s",
            request.url.path,
            exception.status_code,
            exception.code,
        )
        response = ErrorResponse(
            detail=ErrorDetail(
                code=exception.code,
                message=exception.message,
                details=exception.details,
            )
        )
        return JSONResponse(
            status_code=exception.status_code,
            content=response.model_dump(exclude_none=True),
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exception: RequestValidationError,
    ) -> JSONResponse:
        logger.warning(
            "validation_error path=%s count=%s",
            request.url.path,
            len(exception.errors()),
        )
        safe_errors = [
            {
                "type": error["type"],
                "location": list(error["loc"]),
                "message": error["msg"],
            }
            for error in exception.errors()
        ]
        response = ErrorResponse(
            detail=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Os dados enviados são inválidos.",
                details={"errors": safe_errors},
            )
        )
        return JSONResponse(status_code=422, content=response.model_dump(exclude_none=True))

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exception: Exception) -> JSONResponse:
        # O tipo ajuda no diagnóstico; a mensagem pode conter dados do usuário ou segredos.
        logger.error(
            "unexpected_error path=%s type=%s",
            request.url.path,
            type(exception).__name__,
        )
        response = ErrorResponse(
            detail=ErrorDetail(
                code="INTERNAL_ERROR",
                message="Ocorreu um erro interno inesperado.",
            )
        )
        return JSONResponse(status_code=500, content=response.model_dump(exclude_none=True))
