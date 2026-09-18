"""Modelos internos do processamento de documentos."""

from datetime import datetime

from pydantic import BaseModel, Field


class ExtractedSection(BaseModel):
    """Parte textual extraída com sua localização original."""

    content: str
    page: int | None = None


class DocumentChunk(BaseModel):
    """Trecho normalizado pronto para indexação vetorial."""

    id: str
    document_id: str
    document_name: str
    document_type: str
    content: str
    chunk_index: int = Field(ge=0)
    page: int | None = None


class ProcessedDocument(BaseModel):
    """Resultado completo e determinístico do pipeline de ingestão."""

    id: str
    name: str
    document_type: str
    content_hash: str
    file_size: int = Field(ge=0)
    chunks: list[DocumentChunk]


class DocumentResponse(BaseModel):
    """Resumo público de um documento indexado."""

    id: str
    name: str
    document_type: str
    chunk_count: int = Field(ge=0)
    file_size: int = Field(ge=0)
    created_at: datetime


class DocumentTextChunk(BaseModel):
    """Texto indexado sem os vetores usados na busca."""

    content: str
    chunk_index: int = Field(ge=0)
    page: int | None = None


class DocumentContentResponse(BaseModel):
    """Trechos persistidos de um documento, na ordem de leitura."""

    id: str
    chunks: list[DocumentTextChunk]
