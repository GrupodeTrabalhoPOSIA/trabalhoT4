"""Dublês compartilhados pelos testes do backend."""

import math
from datetime import UTC, datetime

from app.core.errors import AppError
from app.models.documents import (
    DocumentContentResponse, DocumentResponse, DocumentTextChunk, ProcessedDocument,
)
from app.models.rag import LLMMessage, RetrievedChunk


class InMemoryVectorStore:
    """Implementa o contrato vetorial sem rede para testes determinísticos."""

    def __init__(self) -> None:
        self.documents: dict[str, tuple[DocumentResponse, str]] = {}
        self.chunks: list[tuple[str, str, str, int, int | None, list[float]]] = []

    def add_document(
        self,
        document: ProcessedDocument,
        embeddings: list[list[float]],
    ) -> DocumentResponse:
        if len(embeddings) != len(document.chunks):
            raise ValueError("Cada chunk deve possuir exatamente um embedding.")
        if document.content_hash in self.known_hashes():
            raise AppError(
                status_code=409,
                code="DUPLICATE_DOCUMENT",
                message="Este documento já existe na base de conhecimento.",
            )

        response = DocumentResponse(
            id=document.id,
            name=document.name,
            document_type=document.document_type,
            chunk_count=len(document.chunks),
            file_size=document.file_size,
            created_at=datetime.now(UTC),
        )
        self.documents[document.id] = (response, document.content_hash)
        self.chunks.extend(
            (
                chunk.document_id,
                chunk.document_name,
                chunk.content,
                chunk.chunk_index,
                chunk.page,
                embedding,
            )
            for chunk, embedding in zip(document.chunks, embeddings, strict=True)
        )
        return response

    def list_documents(self) -> list[DocumentResponse]:
        return sorted(
            (item[0] for item in self.documents.values()),
            key=lambda item: item.created_at,
            reverse=True,
        )

    def get_document_content(self, document_id: str) -> DocumentContentResponse:
        if not self.document_exists(document_id):
            raise AppError(
                status_code=404,
                code="DOCUMENT_NOT_FOUND",
                message="Documento não encontrado.",
            )
        return DocumentContentResponse(
            id=document_id,
            chunks=[
                DocumentTextChunk(content=chunk[2], chunk_index=chunk[3], page=chunk[4])
                for chunk in sorted(self.chunks, key=lambda item: item[3])
                if chunk[0] == document_id
            ],
        )

    def known_hashes(self) -> set[str]:
        return {item[1] for item in self.documents.values()}

    def document_exists(self, document_id: str) -> bool:
        return document_id in self.documents

    def delete_document(self, document_id: str) -> None:
        if not self.document_exists(document_id):
            raise AppError(
                status_code=404,
                code="DOCUMENT_NOT_FOUND",
                message="Documento não encontrado.",
            )
        del self.documents[document_id]
        self.chunks = [chunk for chunk in self.chunks if chunk[0] != document_id]

    def search(
        self,
        embedding: list[float],
        limit: int,
        min_relevance: float,
    ) -> list[RetrievedChunk]:
        matches: list[RetrievedChunk] = []
        for document_id, name, content, index, page, stored_embedding in self.chunks:
            similarity = sum(
                left * right
                for left, right in zip(embedding, stored_embedding, strict=True)
            )
            if similarity < min_relevance:
                continue
            matches.append(
                RetrievedChunk(
                    document_id=document_id,
                    document_name=name,
                    content=content,
                    chunk_index=index,
                    page=page,
                    relevance=max(0.0, min(1.0, similarity)),
                )
            )
        return sorted(matches, key=lambda item: item.relevance, reverse=True)[:limit]


class FakeEmbeddingService:
    """Gera vetores pequenos e determinísticos sem baixar modelos."""

    @staticmethod
    def _embed(text: str) -> list[float]:
        raw = [
            float(len(text)),
            float(sum(character.isalpha() for character in text)),
            float(sum(ord(character) for character in text) % 997),
        ]
        norm = math.sqrt(sum(value * value for value in raw)) or 1.0
        return [value / norm for value in raw]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class FakeLLMClient:
    """Registra o prompt e devolve uma resposta fixa."""

    def __init__(self, answer: str = "Resposta fundamentada da Aurora Tech.") -> None:
        self.answer = answer
        self.calls: list[list[LLMMessage]] = []

    async def complete(self, messages: list[LLMMessage]) -> str:
        self.calls.append(messages)
        return self.answer
