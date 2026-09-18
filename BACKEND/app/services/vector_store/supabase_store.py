"""Armazenamento no Supabase via PostgreSQL Session Pooler e pgvector."""

import json
import math
from datetime import datetime
from typing import Any

from psycopg import Error as PsycopgError
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool, PoolClosed, PoolTimeout

from app.core.errors import AppError
from app.models.documents import (
    DocumentContentResponse,
    DocumentResponse,
    DocumentTextChunk,
    ProcessedDocument,
)
from app.models.rag import RetrievedChunk


class SupabaseVectorStore:
    """Executa SQL parametrizado em um pool pequeno de sessões PostgreSQL."""

    def __init__(
        self,
        database_url: str,
        *,
        min_size: int = 1,
        max_size: int = 5,
        timeout_seconds: float = 10.0,
        pool: ConnectionPool[Any] | Any | None = None,
    ) -> None:
        if pool is not None:
            self.pool = pool
            return

        self.pool = ConnectionPool(
            conninfo=database_url,
            min_size=min_size,
            max_size=max_size,
            timeout=timeout_seconds,
            kwargs={
                "row_factory": dict_row,
                "sslmode": "require",
                "connect_timeout": max(1, math.ceil(timeout_seconds)),
            },
            open=False,
            name="aurora-supabase-session-pool",
        )
        self.pool.open()

    def close(self) -> None:
        """Encerra as sessões mantidas pelo processo do backend."""
        self.pool.close()

    def add_document(
        self,
        document: ProcessedDocument,
        embeddings: list[list[float]],
    ) -> DocumentResponse:
        if len(embeddings) != len(document.chunks):
            raise ValueError("Cada chunk deve possuir exatamente um embedding.")

        chunks = [
            {
                "id": chunk.id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "page": chunk.page,
                "embedding": embedding,
            }
            for chunk, embedding in zip(document.chunks, embeddings, strict=True)
        ]
        try:
            with self.pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select *
                        from public.index_aurora_document(
                            %s::uuid,
                            %s::text,
                            %s::text,
                            %s::text,
                            %s::bigint,
                            %s::jsonb
                        )
                        """,
                        (
                            document.id,
                            document.name,
                            document.document_type,
                            document.content_hash,
                            document.file_size,
                            Jsonb(chunks),
                        ),
                    )
                    row = cursor.fetchone()
        except UniqueViolation as error:
            raise AppError(
                status_code=409,
                code="DUPLICATE_DOCUMENT",
                message="Este documento já existe na base de conhecimento.",
            ) from error
        except (PsycopgError, PoolClosed, PoolTimeout) as error:
            raise self._database_error() from error

        if row is None:
            raise self._database_error()
        return self._document_from_row(row)

    def list_documents(self) -> list[DocumentResponse]:
        try:
            with self.pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select id, name, document_type, chunk_count, file_size, created_at
                        from public.aurora_documents
                        order by created_at desc
                        """
                    )
                    rows = cursor.fetchall()
        except (PsycopgError, PoolClosed, PoolTimeout) as error:
            raise self._database_error() from error
        return [self._document_from_row(row) for row in rows]

    def get_document_content(self, document_id: str) -> DocumentContentResponse:
        try:
            with self.pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select c.content, c.chunk_index, c.page
                        from public.aurora_documents d
                        left join public.aurora_document_chunks c on c.document_id = d.id
                        where d.id = %s::uuid
                        order by c.chunk_index asc
                        """,
                        (document_id,),
                    )
                    rows = cursor.fetchall()
        except (PsycopgError, PoolClosed, PoolTimeout) as error:
            raise self._database_error() from error
        if not rows:
            raise AppError(
                status_code=404,
                code="DOCUMENT_NOT_FOUND",
                message="Documento não encontrado.",
            )
        return DocumentContentResponse(
            id=document_id,
            chunks=[
                DocumentTextChunk(**row) for row in rows if row["chunk_index"] is not None
            ],
        )

    def known_hashes(self) -> set[str]:
        try:
            with self.pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("select content_hash from public.aurora_documents")
                    rows = cursor.fetchall()
        except (PsycopgError, PoolClosed, PoolTimeout) as error:
            raise self._database_error() from error
        return {str(row["content_hash"]) for row in rows}

    def document_exists(self, document_id: str) -> bool:
        try:
            with self.pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select exists(
                            select 1 from public.aurora_documents where id = %s::uuid
                        ) as exists
                        """,
                        (document_id,),
                    )
                    row = cursor.fetchone()
        except (PsycopgError, PoolClosed, PoolTimeout) as error:
            raise self._database_error() from error
        return bool(row and row["exists"])

    def delete_document(self, document_id: str) -> None:
        try:
            with self.pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        delete from public.aurora_documents
                        where id = %s::uuid
                        returning id
                        """,
                        (document_id,),
                    )
                    deleted = cursor.fetchone()
        except (PsycopgError, PoolClosed, PoolTimeout) as error:
            raise self._database_error() from error
        if deleted is None:
            raise AppError(
                status_code=404,
                code="DOCUMENT_NOT_FOUND",
                message="Documento não encontrado.",
            )

    def search(
        self,
        embedding: list[float],
        limit: int,
        min_relevance: float,
    ) -> list[RetrievedChunk]:
        vector = self._vector_literal(embedding)
        try:
            with self.pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select *
                        from public.match_aurora_chunks(
                            %s::extensions.vector,
                            %s::double precision,
                            %s::integer
                        )
                        """,
                        (vector, min_relevance, limit),
                    )
                    rows = cursor.fetchall()
        except (PsycopgError, PoolClosed, PoolTimeout) as error:
            raise self._database_error() from error

        return [
            RetrievedChunk(
                document_id=str(row["document_id"]),
                document_name=str(row["document_name"]),
                content=str(row["content"]),
                chunk_index=int(row["chunk_index"]),
                page=int(row["page"]) if row.get("page") is not None else None,
                relevance=max(0.0, min(1.0, float(row["similarity"]))),
            )
            for row in rows
        ]

    @staticmethod
    def _vector_literal(embedding: list[float]) -> str:
        if not embedding or not all(math.isfinite(value) for value in embedding):
            raise ValueError("O embedding deve conter apenas números finitos.")
        return json.dumps(embedding, separators=(",", ":"))

    @staticmethod
    def _document_from_row(row: dict[str, Any]) -> DocumentResponse:
        created_at = row["created_at"]
        if not isinstance(created_at, datetime):
            created_at = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        return DocumentResponse(
            id=str(row["id"]),
            name=str(row["name"]),
            document_type=str(row["document_type"]),
            chunk_count=int(row["chunk_count"]),
            file_size=int(row["file_size"]),
            created_at=created_at,
        )

    @staticmethod
    def _database_error() -> AppError:
        return AppError(
            status_code=503,
            code="DATABASE_UNAVAILABLE",
            message="A base de conhecimento está temporariamente indisponível.",
        )
