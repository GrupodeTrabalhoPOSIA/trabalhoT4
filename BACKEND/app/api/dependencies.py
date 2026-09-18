"""Construção compartilhada das dependências da API."""

from functools import lru_cache

from app.core.config import get_settings
from app.core.errors import AppError
from app.services.documents import DocumentProcessor, DocumentService
from app.services.embeddings import OpenRouterEmbeddingService
from app.services.llm import OpenRouterClient
from app.services.rag import ChatService, RetrievalService
from app.services.vector_store import SupabaseVectorStore


@lru_cache
def get_embedding_service() -> OpenRouterEmbeddingService:
    settings = get_settings()
    return OpenRouterEmbeddingService(settings)


@lru_cache
def get_vector_store() -> SupabaseVectorStore:
    settings = get_settings()
    try:
        database_url = settings.require_supabase_database_url()
    except ValueError as error:
        raise AppError(
            status_code=503,
            code="DATABASE_NOT_CONFIGURED",
            message="O banco Supabase ainda não foi configurado no backend.",
        ) from error
    return SupabaseVectorStore(
        database_url,
        min_size=settings.supabase_pool_min_size,
        max_size=settings.supabase_pool_max_size,
        timeout_seconds=settings.supabase_pool_timeout_seconds,
    )


def close_dependencies() -> None:
    """Fecha conexões compartilhadas criadas durante a execução da API."""
    get_chat_service.cache_clear()
    get_document_service.cache_clear()
    if get_vector_store.cache_info().currsize:
        get_vector_store().close()
        get_vector_store.cache_clear()


@lru_cache
def get_document_service() -> DocumentService:
    """Cria o serviço real de documentos uma vez por processo."""
    settings = get_settings()
    return DocumentService(
        processor=DocumentProcessor(settings),
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
    )


@lru_cache
def get_chat_service() -> ChatService:
    """Compartilha embeddings e coleção entre ingestão e consulta."""
    settings = get_settings()
    retrieval_service = RetrievalService(
        settings=settings,
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
    )
    return ChatService(
        retrieval_service=retrieval_service,
        llm_client=OpenRouterClient(settings),
    )
