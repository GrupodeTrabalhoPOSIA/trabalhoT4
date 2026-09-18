"""Geração remota de embeddings pela API do OpenRouter."""

import math

import httpx

from app.core.config import Settings
from app.core.errors import AppError

OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"


class OpenRouterEmbeddingService:
    """Gera embeddings em lotes sem expor credenciais ou textos nos erros."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            api_key = self.settings.require_openrouter_api_key()
        except ValueError as exception:
            raise AppError(
                status_code=503,
                code="EMBEDDINGS_NOT_CONFIGURED",
                message="O serviço de embeddings ainda não foi configurado.",
            ) from exception

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.openrouter_referer,
            "X-OpenRouter-Title": self.settings.openrouter_app_title,
        }
        embeddings: list[list[float]] = []

        try:
            with httpx.Client(
                timeout=self.settings.openrouter_timeout_seconds,
                transport=self.transport,
            ) as client:
                for start in range(0, len(texts), self.settings.embedding_batch_size):
                    batch = texts[start : start + self.settings.embedding_batch_size]
                    payload: dict[str, object] = {
                        "model": self.settings.openrouter_embedding_model,
                        "input": batch,
                    }
                    # Mistral Embed possui dimensão fixa; não solicitar redução.
                    if (
                        self.settings.openrouter_embedding_model
                        != "mistralai/mistral-embed-2312"
                    ):
                        payload["dimensions"] = self.settings.embedding_dimensions
                    response = client.post(
                        OPENROUTER_EMBEDDINGS_URL,
                        headers=headers,
                        json=payload,
                    )
                    self._raise_for_provider_error(response.status_code)
                    embeddings.extend(self._parse_response(response, len(batch)))
        except httpx.TimeoutException as exception:
            raise AppError(
                status_code=504,
                code="EMBEDDINGS_TIMEOUT",
                message="A geração dos embeddings demorou demais. Tente novamente.",
            ) from exception
        except httpx.RequestError as exception:
            raise AppError(
                status_code=502,
                code="EMBEDDINGS_CONNECTION_ERROR",
                message="Não foi possível acessar o serviço de embeddings.",
            ) from exception

        return embeddings

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def _parse_response(
        self,
        response: httpx.Response,
        expected_count: int,
    ) -> list[list[float]]:
        try:
            data = response.json()["data"]
            if not isinstance(data, list) or len(data) != expected_count:
                raise ValueError("Quantidade de embeddings inesperada.")

            indexed_vectors: list[tuple[int, list[float]]] = []
            for item in data:
                index = item["index"]
                raw_vector = item["embedding"]
                if not isinstance(index, int) or isinstance(index, bool):
                    raise TypeError("Índice de embedding inválido.")
                if not isinstance(raw_vector, list):
                    raise TypeError("Vetor de embedding inválido.")
                if len(raw_vector) != self.settings.embedding_dimensions:
                    raise ValueError("Dimensão de embedding inesperada.")

                vector: list[float] = []
                for value in raw_vector:
                    if (
                        not isinstance(value, (int, float))
                        or isinstance(value, bool)
                        or not math.isfinite(float(value))
                    ):
                        raise ValueError("Componente de embedding inválido.")
                    vector.append(float(value))
                indexed_vectors.append((index, vector))

            indexed_vectors.sort(key=lambda item: item[0])
            if [index for index, _ in indexed_vectors] != list(range(expected_count)):
                raise ValueError("Índices de embeddings inválidos.")
            return [vector for _, vector in indexed_vectors]
        except (KeyError, TypeError, ValueError) as exception:
            raise AppError(
                status_code=502,
                code="EMBEDDINGS_INVALID_RESPONSE",
                message="O serviço de embeddings retornou um formato inválido.",
            ) from exception

    @staticmethod
    def _raise_for_provider_error(status_code: int) -> None:
        if status_code < 400:
            return
        if status_code in {401, 403}:
            code = "EMBEDDINGS_AUTH_ERROR"
            message = "A autenticação do serviço de embeddings falhou."
        elif status_code == 429:
            code = "EMBEDDINGS_RATE_LIMITED"
            message = "O limite do serviço de embeddings foi atingido. Tente mais tarde."
        elif status_code in {402, 404}:
            code = "EMBEDDINGS_UNAVAILABLE"
            message = "O modelo de embeddings configurado não está disponível."
        else:
            code = "EMBEDDINGS_PROVIDER_ERROR"
            message = "O serviço de embeddings apresentou uma falha."
        raise AppError(status_code=502, code=code, message=message)
