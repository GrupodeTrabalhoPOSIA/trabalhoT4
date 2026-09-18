"""Testes do adaptador Session Pooler sem acessar a rede."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from psycopg.errors import UniqueViolation
from psycopg_pool import PoolTimeout

from app.core.config import Settings
from app.core.errors import AppError
from app.services.documents import DocumentProcessor
from app.services.vector_store import SupabaseVectorStore
from tests.fakes import FakeEmbeddingService

DATABASE_URL = (
    "postgresql://postgres.project:password@aws-0-region.pooler.supabase.com:5432/postgres"
)


def make_document():
    settings = Settings(_env_file=None)
    return DocumentProcessor(settings).process(
        filename="aurora.txt",
        content=b"A Aurora Tech oferece solucoes digitais.",
        content_type="text/plain",
    )


def make_pool(
    *,
    fetchone: object = None,
    fetchall: list[dict[str, object]] | None = None,
) -> tuple[MagicMock, MagicMock]:
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone
    cursor.fetchall.return_value = fetchall or []
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    pool = MagicMock()
    pool.connection.return_value.__enter__.return_value = connection
    return pool, cursor


def test_indexes_document_atomically_through_postgres_function() -> None:
    document = make_document()
    embeddings = FakeEmbeddingService().embed_documents(
        [chunk.content for chunk in document.chunks]
    )
    pool, cursor = make_pool(
        fetchone={
            "id": document.id,
            "name": document.name,
            "document_type": document.document_type,
            "chunk_count": 1,
            "file_size": document.file_size,
            "created_at": datetime(2026, 8, 28, 12, 0, tzinfo=UTC),
        }
    )
    store = SupabaseVectorStore(DATABASE_URL, pool=pool)

    indexed = store.add_document(document, embeddings)

    query, parameters = cursor.execute.call_args.args
    assert "public.index_aurora_document" in query
    assert parameters[0] == document.id
    assert parameters[3] == document.content_hash
    assert indexed.id == document.id
    assert indexed.chunk_count == 1


def test_search_passes_threshold_to_pgvector_and_maps_source() -> None:
    pool, cursor = make_pool(
        fetchall=[
            {
                "document_id": "5d5d6b09-9444-4cf6-b3da-b3e663983dfa",
                "document_name": "servicos.txt",
                "content": "Consultoria em transformação digital.",
                "chunk_index": 0,
                "page": None,
                "similarity": 0.87,
            }
        ]
    )
    store = SupabaseVectorStore(DATABASE_URL, pool=pool)

    chunks = store.search([0.1, 0.2, 0.3], limit=5, min_relevance=0.35)

    query, parameters = cursor.execute.call_args.args
    assert "public.match_aurora_chunks" in query
    assert parameters == ("[0.1,0.2,0.3]", 0.35, 5)
    assert chunks[0].document_name == "servicos.txt"
    assert chunks[0].relevance == 0.87


def test_lists_documents_from_session_pooler() -> None:
    pool, _ = make_pool(
        fetchall=[
            {
                "id": "5d5d6b09-9444-4cf6-b3da-b3e663983dfa",
                "name": "empresa.md",
                "document_type": "md",
                "chunk_count": 2,
                "file_size": 321,
                "created_at": datetime(2026, 8, 28, 12, 0, tzinfo=UTC),
            }
        ]
    )
    store = SupabaseVectorStore(DATABASE_URL, pool=pool)

    documents = store.list_documents()

    assert documents[0].name == "empresa.md"
    assert documents[0].chunk_count == 2


def test_duplicate_constraint_is_exposed_as_domain_error() -> None:
    document = make_document()
    embeddings = FakeEmbeddingService().embed_documents(
        [chunk.content for chunk in document.chunks]
    )
    pool, cursor = make_pool()
    cursor.execute.side_effect = UniqueViolation("duplicate")
    store = SupabaseVectorStore(DATABASE_URL, pool=pool)

    with pytest.raises(AppError) as captured:
        store.add_document(document, embeddings)

    assert captured.value.status_code == 409
    assert captured.value.code == "DUPLICATE_DOCUMENT"


def test_close_releases_pool_connections() -> None:
    pool, _ = make_pool()
    store = SupabaseVectorStore(DATABASE_URL, pool=pool)

    store.close()

    pool.close.assert_called_once_with()


def test_reads_content_without_vectors_in_document_order() -> None:
    pool, cursor = make_pool(fetchall=[
        {"content": "Primeiro trecho.", "chunk_index": 0, "page": None},
        {"content": "Segundo trecho.", "chunk_index": 1, "page": None},
    ])
    store = SupabaseVectorStore(DATABASE_URL, pool=pool)
    document_id = "5d5d6b09-9444-4cf6-b3da-b3e663983dfa"

    result = store.get_document_content(document_id)

    query, parameters = cursor.execute.call_args.args
    assert parameters == (document_id,)
    assert "where d.id = %s::uuid" in query
    assert "order by c.chunk_index asc" in query
    assert "embedding" not in query
    assert result.id == document_id
    assert [chunk.content for chunk in result.chunks] == ["Primeiro trecho.", "Segundo trecho."]


def test_content_missing_document_returns_404() -> None:
    pool, _ = make_pool()
    with pytest.raises(AppError) as captured:
        SupabaseVectorStore(DATABASE_URL, pool=pool).get_document_content("missing")
    assert captured.value.status_code == 404


def test_content_database_failure_returns_safe_error() -> None:
    pool, cursor = make_pool()
    cursor.execute.side_effect = PoolTimeout("sensitive connection detail")
    with pytest.raises(AppError) as captured:
        SupabaseVectorStore(DATABASE_URL, pool=pool).get_document_content("document")
    assert captured.value.status_code == 503
    assert "sensitive" not in captured.value.message


def test_content_existing_document_with_no_chunks_is_empty() -> None:
    pool, _ = make_pool(fetchall=[{"content": None, "chunk_index": None, "page": None}])
    result = SupabaseVectorStore(DATABASE_URL, pool=pool).get_document_content("document")
    assert result.chunks == []
