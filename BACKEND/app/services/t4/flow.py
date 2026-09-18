"""Fluxo executável do Trabalho 4: roteamento, contexto mínimo, validação e fallback."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.models.rag import LLMMessage
from app.services.llm import LLMClient

Route = Literal["TRH-01", "TRH-02", "TRH-03", "FORA_ESCOPO"]

PROMPT_VERSIONS = {"TRH-01": "v0.3", "TRH-02": "v0.1", "TRH-03": "v0.1", "TRH-04": "v0.1"}

@dataclass(frozen=True)
class FlowResult:
    answer: str
    route: Route
    prompt_id: str
    prompt_version: str
    valid: bool
    retries: int
    latency_ms: int
    status: str

class PromptRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self, prompt_id: str, version: str) -> str:
        path = self.root / f"{prompt_id}_{version}.txt"
        if not path.is_file():
            raise FileNotFoundError(f"Prompt não encontrado: {path.name}")
        return path.read_text(encoding="utf-8")

class T4FlowService:
    """Orquestra os templates do T3 sem substituir o serviço RAG existente."""
    def __init__(self, *, llm_client: LLMClient, prompt_registry: PromptRegistry, knowledge_base: str) -> None:
        self.llm_client = llm_client
        self.prompts = prompt_registry
        self.knowledge_base = knowledge_base.strip()

    async def run(self, question: str) -> FlowResult:
        started = time.perf_counter()
        clean = question.strip()
        if not clean:
            return self._result("Informe uma pergunta para continuar.", "FORA_ESCOPO", "TRH-04", False, 0, started, "entrada_invalida")

        route, route_retries = await self._route(clean)
        if route == "FORA_ESCOPO":
            return self._result(
                "A pergunta está fora do escopo do Copiloto de RH da política-piloto Aurora Tech. Dúvidas sobre a política devem ser encaminhadas ao RH Responde.",
                route, "TRH-04", True, route_retries, started, "recusado_fora_escopo"
            )

        if route == "TRH-02" and self._eligibility_data_missing(clean):
            return self._result(
                "Para verificar a elegibilidade, informe sua função ou contexto de trabalho.",
                route, "TRH-02", True, route_retries, started, "perguntar_dado_ausente"
            )

        answer, specialist_retries, valid = await self._specialist(route, clean)
        retries = route_retries + specialist_retries
        if not valid:
            answer = "Não foi possível validar a resposta com segurança. Encaminhe a dúvida ao RH Responde."
            status = "fallback_validacao"
        else:
            status = "respondido"
        return self._result(answer, route, route, valid, retries, started, status)

    async def _route(self, question: str) -> tuple[Route, int]:
        prompt = self.prompts.load("TRH-04", PROMPT_VERSIONS["TRH-04"])
        messages: list[LLMMessage] = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ]
        for attempt in range(2):
            raw = await self.llm_client.complete(messages)
            route = self._parse_route(raw)
            if route is not None:
                return route, attempt
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": "Formato inválido. Repita somente o JSON exigido."})
        return "FORA_ESCOPO", 1

    @staticmethod
    def _parse_route(raw: str) -> Route | None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        route = data.get("prompt_destino")
        confidence = data.get("confianca")
        if route not in {"TRH-01", "TRH-02", "TRH-03", "FORA_ESCOPO"}:
            return None
        if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
            return None
        return route

    async def _specialist(self, route: Route, question: str) -> tuple[str, int, bool]:
        prompt = self.prompts.load(route, PROMPT_VERSIONS[route])
        system = f"{prompt}\n\nBASE DE CONHECIMENTO:\n{self.knowledge_base}"
        messages: list[LLMMessage] = [{"role": "system", "content": system}, {"role": "user", "content": question}]
        for attempt in range(2):
            raw = (await self.llm_client.complete(messages)).strip()
            if self._valid_specialist_output(route, raw):
                return raw, attempt, True
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": "A saída não seguiu o formato obrigatório. Corrija uma única vez, sem acrescentar fatos."})
        return raw, 1, False

    @staticmethod
    def _valid_specialist_output(route: Route, raw: str) -> bool:
        required = ["Resposta:", "Regra aplicada:", "Próximo passo:"]
        if route == "TRH-02":
            required.insert(0, "Classificação:")
            match = re.search(r"Classificação:\s*(.+)", raw, re.IGNORECASE)
            if not match or match.group(1).strip().lower() not in {"elegível", "não elegível", "consultar rh"}:
                return False
        return all(label.lower() in raw.lower() for label in required)

    @staticmethod
    def _eligibility_data_missing(question: str) -> bool:
        q = question.lower()
        asks_eligibility = any(term in q for term in ("elegível", "elegivel", "posso aderir", "posso trabalhar remot"))
        known_function = any(term in q for term in ("atendimento presencial", "laboratório", "laboratorio", "manutenção", "manutencao", "minha função", "minha funcao", "trabalho como"))
        return asks_eligibility and not known_function

    @staticmethod
    def _result(answer: str, route: Route, prompt_id: str, valid: bool, retries: int, started: float, status: str) -> FlowResult:
        return FlowResult(answer=answer, route=route, prompt_id=prompt_id, prompt_version=PROMPT_VERSIONS[prompt_id], valid=valid, retries=retries, latency_ms=round((time.perf_counter()-started)*1000), status=status)
