"""Endpoint do chat fundamentado pela base de conhecimento."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_chat_service
from app.models.chat import ChatRequest, ChatResponse
from app.models.errors import ErrorResponse
from app.services.rag import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
ChatServiceDependency = Annotated[ChatService, Depends(get_chat_service)]


@router.post(
    "",
    response_model=ChatResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Dados de entrada inválidos."},
        502: {"model": ErrorResponse, "description": "Falha no provedor do modelo."},
        503: {"model": ErrorResponse, "description": "Modelo não configurado."},
        504: {"model": ErrorResponse, "description": "Tempo de resposta excedido."},
    },
    summary="Enviar uma pergunta ao assistente",
)
async def send_message(
    request: ChatRequest,
    service: ChatServiceDependency,
) -> ChatResponse:
    """Responde apenas quando houver contexto relevante na coleção."""
    return await service.answer(request)
