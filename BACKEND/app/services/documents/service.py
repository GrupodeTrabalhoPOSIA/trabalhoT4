"""Orquestra processamento, embeddings e persistência de documentos."""

from app.models.documents import DocumentContentResponse, DocumentResponse
from app.services.documents.processor import DocumentProcessor
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


class DocumentService:
    """Caso de uso da base de conhecimento."""

    def __init__(
        self,
        *,
        processor: DocumentProcessor,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ) -> None:
        self.processor = processor
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def index_document(
        self,
        *,
        filename: str,
        content: bytes,
        content_type: str | None,
    ) -> DocumentResponse:
        document = self.processor.process(
            filename=filename,
            content=content,
            content_type=content_type,
            known_hashes=self.vector_store.known_hashes(),
        )
        embeddings = self.embedding_service.embed_documents(
            [chunk.content for chunk in document.chunks]
        )
        return self.vector_store.add_document(document, embeddings)

    def list_documents(self) -> list[DocumentResponse]:
        return self.vector_store.list_documents()

    def get_document_content(self, document_id: str) -> DocumentContentResponse:
        return self.vector_store.get_document_content(document_id)

    def delete_document(self, document_id: str) -> None:
        self.vector_store.delete_document(document_id)
