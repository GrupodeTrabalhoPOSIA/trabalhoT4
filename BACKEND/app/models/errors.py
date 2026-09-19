"""Contrato padronizado de erro da API."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ProviderDiagnostic(BaseModel):
    """Somente números e categorias autorizadas; nunca texto livre do provedor."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    http_status: int = Field(ge=400, le=599)
    source: Literal["openrouter", "provider", "unknown"] = "unknown"
    reason: Literal[
        "rate_limit", "capacity", "quota", "credits", "key_credit_limit",
        "in_flight_budget", "request_budget", "unknown",
    ] = "unknown"
    retry_after_seconds: int | None = Field(default=None, ge=0)

    @computed_field
    @property
    def message(self) -> str:
        return {
            "rate_limit": "Limite de requisições atingido. Isso pode ocorrer mesmo com saldo disponível.",
            "capacity": "O serviço informou capacidade temporariamente esgotada.",
            "quota": "O serviço informou uma cota esgotada. Confira os limites da conta ou do provedor.",
            "credits": "Limite financeiro atingido. Confira o saldo e o orçamento disponível para a requisição.",
            "key_credit_limit": "O limite de gastos desta chave foi atingido; o saldo da conta pode continuar positivo.",
            "in_flight_budget": "O orçamento para chamadas em andamento ou em liquidação foi atingido; isso não significa saldo zerado.",
            "request_budget": "O custo estimado desta requisição ultrapassa o orçamento disponível por chamada.",
            "unknown": "O serviço retornou um erro sem uma causa específica reconhecida no diagnóstico seguro.",
        }[self.reason]


class ErrorDetail(BaseModel):
    """Detalhes legíveis e identificáveis de um erro."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Envelope de erro retornado por todos os endpoints."""

    detail: ErrorDetail

