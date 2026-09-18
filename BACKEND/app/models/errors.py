"""Contrato padronizado de erro da API."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    """Detalhes legíveis e identificáveis de um erro."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Envelope de erro retornado por todos os endpoints."""

    detail: ErrorDetail

