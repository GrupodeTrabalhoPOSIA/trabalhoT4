"""Cliente HTTP isolado para a API do OpenRouter."""

import logging
from typing import Any

import httpx

from app.core.config import Settings
from app.core.errors import AppError
from app.models.rag import LLMMessage
from app.services.llm.provider_errors import diagnose_provider_error, normalize_provider_response

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
logger = logging.getLogger("aurora.openrouter")


class OpenRouterClient:
    """Executa chat completions sem expor credenciais nos erros."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    async def complete(self, messages: list[LLMMessage]) -> str:
        try:
            api_key = self.settings.require_openrouter_api_key()
        except ValueError as exception:
            raise AppError(
                status_code=503,
                code="MODEL_NOT_CONFIGURED",
                message="O serviço de respostas ainda não foi configurado.",
            ) from exception

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.openrouter_referer,
            "X-OpenRouter-Title": self.settings.openrouter_app_title,
        }
        payload: dict[str, Any] = {
            "model": self.settings.openrouter_model,
            "messages": messages,
            "temperature": self.settings.openrouter_temperature,
            "max_tokens": self.settings.openrouter_max_tokens,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.openrouter_timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(
                    OPENROUTER_CHAT_URL,
                    headers=headers,
                    json=payload,
                )
        except httpx.TimeoutException as exception:
            raise AppError(
                status_code=504,
                code="MODEL_TIMEOUT",
                message="O modelo demorou demais para responder. Tente novamente.",
            ) from exception
        except httpx.RequestError as exception:
            raise AppError(
                status_code=502,
                code="MODEL_CONNECTION_ERROR",
                message="Não foi possível acessar o serviço de respostas.",
            ) from exception

        self._raise_for_provider_error(response)
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exception:
            raise AppError(
                status_code=502,
                code="MODEL_INVALID_RESPONSE",
                message="O serviço de respostas retornou um formato inválido.",
            ) from exception

        if not isinstance(content, str) or not content.strip():
            raise AppError(
                status_code=502,
                code="MODEL_INVALID_RESPONSE",
                message="O serviço de respostas retornou uma resposta vazia.",
            )
        return content.strip()

    @staticmethod
    def _raise_for_provider_error(response: httpx.Response) -> None:
        response = normalize_provider_response(response)
        status_code = response.status_code
        if status_code < 400:
            return
        diagnostic = diagnose_provider_error(response)
        if status_code in {401, 403}:
            code = "MODEL_AUTH_ERROR"
            message = "A autenticação do serviço de respostas falhou."
        elif status_code == 429:
            code = "MODEL_RATE_LIMITED"
            message = diagnostic.message
        elif status_code == 402:
            code = "MODEL_CREDIT_LIMIT"
            message = diagnostic.message
        elif status_code == 404:
            code = "MODEL_UNAVAILABLE"
            message = "O modelo configurado não está disponível."
        else:
            code = "MODEL_PROVIDER_ERROR"
            message = "O serviço de respostas apresentou uma falha."
        logger.warning("model_provider_error code=%s diagnostic=%s", code, diagnostic.model_dump(exclude_none=True))
        raise AppError(status_code=502, code=code, message=message, diagnostic=diagnostic)
