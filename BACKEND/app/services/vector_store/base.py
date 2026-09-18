"""Contrato do armazenamento vetorial usado pelos casos de uso."""

from typing import Protocol

from app.models.documents import DocumentContentResponse, DocumentResponse, ProcessedDocument
from app.models.rag import RetrievedChunk


class VectorStore(Protocol):
    """Permite trocar o provedor sem acoplar os serviços de domínio."""

    def add_document(
        self,
        document: ProcessedDocument,
        embeddings: list[list[float]],
    ) -> DocumentResponse: ...

    def list_documents(self) -> list[DocumentResponse]: ...

    def get_document_content(self, document_id: str) -> DocumentContentResponse: ...

    def known_hashes(self) -> set[str]: ...

    def document_exists(self, document_id: str) -> bool: ...

    def delete_document(self, document_id: str) -> None: ...

    def search(
        self,
        embedding: list[float],
        limit: int,
        min_relevance: float,
    ) -> list[RetrievedChunk]: ...
