"""Endpoint de verificação de saúde da API."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Resposta do endpoint de saúde."""

    status: Literal["ok"]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verificar a saúde da API",
)
async def health_check() -> HealthResponse:
    """Confirma que o processo da API está disponível."""
    return HealthResponse(status="ok")

