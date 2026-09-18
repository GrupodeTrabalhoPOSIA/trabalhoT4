"""Endpoints da base de conhecimento."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from app.api.dependencies import get_document_service
from app.core.config import get_settings
from app.models.documents import DocumentContentResponse, DocumentResponse
from app.models.errors import ErrorResponse
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])

DocumentServiceDependency = Annotated[DocumentService, Depends(get_document_service)]


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Documento duplicado."},
        413: {"model": ErrorResponse, "description": "Arquivo acima do limite."},
        415: {"model": ErrorResponse, "description": "Formato inválido."},
        422: {"model": ErrorResponse, "description": "Conteúdo inválido ou vazio."},
        502: {"model": ErrorResponse, "description": "Falha no provedor de embeddings."},
        503: {"model": ErrorResponse, "description": "Embeddings não configurados."},
        504: {"model": ErrorResponse, "description": "Geração de embeddings excedeu o tempo."},
    },
    summary="Indexar um documento",
)
async def upload_document(
    service: DocumentServiceDependency,
    file: Annotated[UploadFile, File(description="PDF, TXT, Markdown ou DOCX")],
) -> DocumentResponse:
    """Processa e indexa o arquivo fora do loop assíncrono da API."""
    settings = get_settings()
    content = await file.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    return await run_in_threadpool(
        service.index_document,
        filename=file.filename or "",
        content=content,
        content_type=file.content_type,
    )


@router.get("", response_model=list[DocumentResponse], summary="Listar documentos")
async def list_documents(service: DocumentServiceDependency) -> list[DocumentResponse]:
    return service.list_documents()


@router.get(
    "/{document_id}/content",
    response_model=DocumentContentResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Documento inexistente."},
        503: {"model": ErrorResponse, "description": "Base indisponível."},
    },
    summary="Ler o texto indexado de um documento",
)
def get_document_content(
    document_id: UUID, service: DocumentServiceDependency,
) -> DocumentContentResponse:
    return service.get_document_content(str(document_id))


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse, "description": "Documento inexistente."}},
    summary="Remover um documento",
)
async def delete_document(document_id: str, service: DocumentServiceDependency) -> None:
    service.delete_document(document_id)
