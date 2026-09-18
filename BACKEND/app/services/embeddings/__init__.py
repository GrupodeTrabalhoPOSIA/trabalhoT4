"""Serviços de geração de embeddings."""

from app.services.embeddings.base import EmbeddingService
from app.services.embeddings.openrouter import OpenRouterEmbeddingService

__all__ = ["EmbeddingService", "OpenRouterEmbeddingService"]
