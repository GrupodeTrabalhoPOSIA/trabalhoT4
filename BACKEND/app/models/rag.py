"""Modelos internos da recuperação e da comunicação com o LLM."""

from typing import Literal, TypedDict

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    """Trecho recuperado do banco vetorial com relevância normalizada."""

    document_id: str
    document_name: str
    content: str
    chunk_index: int = Field(ge=0)
    page: int | None = None
    relevance: float = Field(ge=0, le=1)


class LLMMessage(TypedDict):
    """Mensagem compatível com o endpoint de chat completions."""

    role: Literal["system", "user", "assistant"]
    content: str
