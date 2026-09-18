"""Testes das configurações do backend."""

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


def test_settings_have_safe_academic_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.frontend_origin == "http://localhost:5173"
    assert settings.retrieval_top_k == 5
    assert settings.max_upload_size_mb == 10
    assert settings.openrouter_api_key is None
    assert settings.openrouter_embedding_model == "mistralai/mistral-embed-2312"
    assert settings.embedding_dimensions == 1024
    assert settings.embedding_batch_size == 64


def test_openrouter_key_is_masked() -> None:
    settings = Settings(_env_file=None, openrouter_api_key="segredo-de-teste")

    assert isinstance(settings.openrouter_api_key, SecretStr)
    assert "segredo-de-teste" not in repr(settings)
    assert settings.require_openrouter_api_key() == "segredo-de-teste"


def test_mistral_requires_1024_dimensions() -> None:
    with pytest.raises(ValidationError, match="EMBEDDING_DIMENSIONS=1024"):
        Settings(_env_file=None, embedding_dimensions=384)


def test_openrouter_key_is_validated_only_when_used() -> None:
    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        settings.require_openrouter_api_key()


def test_supabase_session_pooler_url_is_masked() -> None:
    settings = Settings(
        _env_file=None,
        supabase_db_url=(
            "postgresql://postgres.project:segredo-do-banco@"
            "aws-0-region.pooler.supabase.com:5432/postgres"
        ),
    )

    assert "segredo-do-banco" not in repr(settings)
    assert settings.require_supabase_database_url().startswith(
        "postgresql://postgres.project:"
    )


def test_supabase_database_url_is_validated_only_when_used() -> None:
    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="SUPABASE_DB_URL"):
        settings.require_supabase_database_url()


def test_supabase_transaction_pooler_is_rejected() -> None:
    settings = Settings(
        _env_file=None,
        supabase_db_url=(
            "postgresql://postgres.project:password@"
            "aws-0-region.pooler.supabase.com:6543/postgres"
        ),
    )

    with pytest.raises(ValueError, match="Session Pooler"):
        settings.require_supabase_database_url()


def test_supabase_pool_minimum_cannot_exceed_maximum() -> None:
    with pytest.raises(ValidationError, match="SUPABASE_POOL_MIN_SIZE"):
        Settings(
            _env_file=None,
            supabase_pool_min_size=6,
            supabase_pool_max_size=5,
        )


def test_chunk_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(ValidationError, match="CHUNK_OVERLAP"):
        Settings(_env_file=None, chunk_size=500, chunk_overlap=500)
