"""Clientes de modelos de linguagem."""

from app.services.llm.base import LLMClient
from app.services.llm.openrouter import OpenRouterClient

__all__ = ["LLMClient", "OpenRouterClient"]
