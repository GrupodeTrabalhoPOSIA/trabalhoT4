"""Contrato do provedor de embeddings."""

from typing import Protocol


class EmbeddingService(Protocol):
    """Abstração que mantém o restante do sistema independente do modelo."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Gera vetores para os trechos que serão indexados."""

    def embed_query(self, text: str) -> list[float]:
        """Gera um vetor para uma consulta de busca."""

