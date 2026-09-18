"""Contrato do provedor de modelo de linguagem."""

from typing import Protocol

from app.models.rag import LLMMessage


class LLMClient(Protocol):
    """Abstração assíncrona do modelo usado pelo chat."""

    async def complete(self, messages: list[LLMMessage]) -> str:
        """Gera uma resposta textual para a conversa informada."""
