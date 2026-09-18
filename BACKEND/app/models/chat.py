"""Contratos HTTP do chat."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_MESSAGES = 10


class ChatHistoryMessage(BaseModel):
    """Mensagem anterior enviada apenas para contexto temporário."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("A mensagem não pode conter apenas espaços.")
        return cleaned


class ChatRequest(BaseModel):
    """Pergunta atual e histórico curto mantido pelo frontend."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "message": "Quais serviços a Aurora Tech oferece?",
                    "history": [
                        {"role": "user", "content": "O que é a Aurora Tech?"},
                        {"role": "assistant", "content": "A Aurora Tech é..."},
                    ],
                }
            ]
        },
    )

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    history: list[ChatHistoryMessage] = Field(
        default_factory=list,
        max_length=MAX_HISTORY_MESSAGES,
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("A pergunta não pode conter apenas espaços.")
        return cleaned


class ChatSource(BaseModel):
    """Documento utilizado para fundamentar uma resposta."""

    document_id: str
    document_name: str
    page: int | None = None


class ChatResponse(BaseModel):
    """Resposta final entregue ao frontend."""

    answer: str
    sources: list[ChatSource] = Field(default_factory=list)
    has_context: bool

