"""Configuração tipada da aplicação a partir do ambiente."""

from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações do backend, carregadas de variáveis de ambiente ou `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Aurora Tech Chatbot API"
    app_version: str = "0.1.0"
    frontend_origin: str = "http://localhost:5173"
    log_level: str = "INFO"

    openrouter_api_key: SecretStr | None = None
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    openrouter_max_tokens: int = Field(default=500, ge=50, le=4000)
    openrouter_temperature: float = Field(default=0.1, ge=0, le=2)
    openrouter_referer: str = "http://localhost:5173"
    openrouter_app_title: str = "Aurora Tech Chatbot"
    openrouter_embedding_model: str = "mistralai/mistral-embed-2312"
    embedding_dimensions: int = Field(default=1024, ge=1, le=3072)
    embedding_batch_size: int = Field(default=64, ge=1, le=256)

    supabase_db_url: SecretStr | None = None
    supabase_pool_min_size: int = Field(default=1, ge=0, le=10)
    supabase_pool_max_size: int = Field(default=5, ge=1, le=20)
    supabase_pool_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    retrieval_min_relevance: float = Field(default=0.35, ge=0, le=1)
    max_context_characters: int = Field(default=6000, ge=500, le=30000)
    chunk_size: int = Field(default=700, ge=100, le=4000)
    chunk_overlap: int = Field(default=100, ge=0, le=1000)

    max_message_length: int = Field(default=2000, ge=100, le=20000)
    max_history_messages: int = Field(default=10, ge=0, le=50)
    max_upload_size_mb: int = Field(default=10, ge=1, le=100)

    @field_validator(
        "openrouter_api_key",
        "supabase_db_url",
        mode="before",
    )
    @classmethod
    def empty_configuration_is_none(cls, value: object) -> object:
        """Trata valores vazios do arquivo de exemplo como ausentes."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def validate_chunk_configuration(self) -> "Settings":
        """Valida relações entre limites configuráveis."""
        if (
            self.openrouter_embedding_model == "mistralai/mistral-embed-2312"
            and self.embedding_dimensions != 1024
        ):
            raise ValueError("Mistral Embed 2312 exige EMBEDDING_DIMENSIONS=1024.")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP deve ser menor que CHUNK_SIZE.")
        if self.supabase_pool_min_size > self.supabase_pool_max_size:
            raise ValueError(
                "SUPABASE_POOL_MIN_SIZE deve ser menor ou igual a "
                "SUPABASE_POOL_MAX_SIZE."
            )
        return self

    def require_openrouter_api_key(self) -> str:
        """Retorna a chave ou falha apenas quando a integração for utilizada."""
        if self.openrouter_api_key is None:
            raise ValueError("OPENROUTER_API_KEY não foi configurada.")
        return self.openrouter_api_key.get_secret_value()

    def require_supabase_database_url(self) -> str:
        """Retorna a URI secreta do Session Pooler quando o banco for utilizado."""
        if self.supabase_db_url is None:
            raise ValueError("SUPABASE_DB_URL não foi configurada.")
        database_url = self.supabase_db_url.get_secret_value()
        parsed = urlparse(database_url)
        try:
            port = parsed.port
        except ValueError as error:
            raise ValueError("SUPABASE_DB_URL possui uma porta inválida.") from error
        if (
            parsed.scheme not in {"postgres", "postgresql"}
            or not parsed.hostname
            or not parsed.hostname.endswith(".pooler.supabase.com")
            or port != 5432
        ):
            raise ValueError(
                "SUPABASE_DB_URL deve usar o Session Pooler do Supabase na porta 5432."
            )
        return database_url


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância compartilhada e imutável durante a execução."""
    return Settings()
