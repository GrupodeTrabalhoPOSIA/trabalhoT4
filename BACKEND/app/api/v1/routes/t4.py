"""Protótipo acadêmico integrado, independente da coleção RAG de uploads."""

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings
from app.services.llm import OpenRouterClient
from app.services.t4.flow import PROMPT_VERSIONS, PromptRegistry, T4FlowService

router = APIRouter(prefix="/t4", tags=["Trabalho 4"])


class FlowRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    correction: str = Field(default="", max_length=2000)
    mode: Literal["real", "invalid_router", "invalid_specialist"] = "real"

    @field_validator("question")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Informe uma pergunta.")
        return value.strip()


def get_t4_service() -> T4FlowService:
    # No terminal e no Docker o diretório de trabalho é a raiz do BACKEND.
    return T4FlowService(
        llm_client=OpenRouterClient(get_settings()),
        prompt_registry=PromptRegistry(Path("prompts/templates")),
        knowledge_base=Path("knowledge/politica_aurora_tech.txt").read_text(encoding="utf-8"),
    )


class SimulatedClient:
    """Erros didáticos explícitos: nunca chama o provedor nem consome créditos."""

    def __init__(self, mode: str) -> None:
        route = '{"prompt_destino":"TRH-01","confianca":0.98,"motivo":"regra"}'
        answer = "Resposta: Até dois dias por semana.\nRegra aplicada: Colaboradores elegíveis poderão trabalhar remotamente até dois dias por semana, definidos com o gestor.\nPróximo passo: Definir os dias com o gestor."
        self.outputs = iter(["JSON inválido", route, answer] if mode == "invalid_router" else [route, "Saída sem campos", "Ainda sem contrato"])

    async def complete(self, messages) -> str:
        return next(self.outputs)


@router.get("/config")
def configuration():
    settings = get_settings()
    return {
        "model": settings.openrouter_model,
        "embedding_model": settings.openrouter_embedding_model,
        "baseline_model": settings.baseline_model,
        "temperature": settings.openrouter_temperature,
        "max_tokens": settings.openrouter_max_tokens,
        "prompts": PROMPT_VERSIONS,
        "knowledge_base": Path("knowledge/politica_aurora_tech.txt").read_text(encoding="utf-8"),
        "prompt_provenance": "Templates reconstruídos a partir do relatório T3; conferência com originais pendente.",
    }


@router.post("/run")
async def run_flow(request: FlowRequest, service: Annotated[T4FlowService, Depends(get_t4_service)]):
    if request.mode != "real":
        service = T4FlowService(llm_client=SimulatedClient(request.mode), prompt_registry=service.prompts, knowledge_base=service.knowledge_base)
    effective_question = request.correction.strip() or request.question
    result = await service.run(effective_question)
    return {
        **asdict(result),
        "execution_id": str(uuid4()),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "question": request.question,
        "effective_question": effective_question,
        "correction_applied": bool(request.correction.strip()),
        "mode": request.mode,
        "model": get_settings().openrouter_model if request.mode == "real" else "simulação determinística",
        "temperature": get_settings().openrouter_temperature if request.mode == "real" else None,
        "max_tokens": get_settings().openrouter_max_tokens if request.mode == "real" else None,
    }
