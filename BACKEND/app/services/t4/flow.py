"""Fluxo executável do Trabalho 4: roteamento, contexto mínimo, validação e fallback."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from app.models.rag import LLMMessage
from app.services.llm import LLMClient
from app.core.errors import AppError

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
    trace: list[dict[str, str]] = field(default_factory=list)
    attempts: list[dict[str, str | int]] = field(default_factory=list)
    context: str = ""

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
        trace: list[dict[str, str]] = []
        attempts: list[dict[str, str | int]] = []
        retries = 0
        context = ""

        def step(id: str, state: str, detail: str) -> None:
            trace.append({"id": id, "state": state, "detail": detail})

        def finish(answer: str, route: Route, prompt_id: str, valid: bool, status: str) -> FlowResult:
            step("outcome", "completed" if valid else "warning", status)
            return FlowResult(answer, route, prompt_id, PROMPT_VERSIONS[prompt_id], valid,
                              retries, round((time.perf_counter() - started) * 1000), status,
                              trace, attempts, context)

        async def generate(messages: list[LLMMessage], phase: str, validator):
            nonlocal retries
            while True:
                try:
                    raw = await self.llm_client.complete(messages)
                    accepted = validator(raw)
                    attempts.append({"phase": phase, "output": raw, "error": "" if accepted else "INVALID_FORMAT"})
                    if accepted:
                        return raw
                except AppError as error:
                    attempts.append({"phase": phase, "output": "", "error": error.code})
                    if error.code not in {"MODEL_TIMEOUT", "MODEL_CONNECTION_ERROR", "MODEL_PROVIDER_ERROR", "MODEL_INVALID_RESPONSE"}:
                        return None
                if retries >= 1:
                    return None
                retries += 1
                step(phase, "warning", "Falha na chamada ou no formato. Uma repetição controlada.")
                messages = [*messages, {"role": "user", "content": "Repita a resposta respeitando exatamente o contrato de saída, usando somente a base fornecida."}]

        if not clean:
            step("input", "failed", "Pergunta vazia.")
            return finish("Informe uma pergunta para continuar.", "FORA_ESCOPO", "TRH-04", False, "entrada_invalida")

        step("input", "completed", "Pergunta atual validada. Histórico anterior não é enviado ao modelo.")
        routing_prompt = self.prompts.load("TRH-04", PROMPT_VERSIONS["TRH-04"])
        raw_route = await generate([
            {"role": "system", "content": routing_prompt},
            {"role": "user", "content": clean},
        ], "routing", lambda raw: self._parse_route(raw) is not None)
        if raw_route is None:
            step("routing", "failed", "Roteamento não validado. Especialista não foi chamado.")
            return finish("Não foi possível classificar a pergunta com segurança. Tente novamente mais tarde ou consulte o RH Responde.", "FORA_ESCOPO", "TRH-04", False, "fallback_roteamento")
        decision = json.loads(raw_route)
        route: Route = decision["prompt_destino"]
        step("routing", "completed", f"TRH-04 v0.1 → {route}; confiança {decision['confianca']:.0%}.")
        if decision["confianca"] < 0.7:
            step("data", "warning", "Confiança inferior a 70%; aguardando esclarecimento.")
            return finish("Você quer esclarecer uma regra, verificar sua elegibilidade ou tratar de segurança? Reformule a pergunta com esse contexto.", route, "TRH-04", True, "perguntar_ambiguidade")
        if route == "FORA_ESCOPO":
            step("data", "warning", "Pedido fora das tarefas autorizadas.")
            return finish(
                "A pergunta está fora do escopo do Copiloto de RH da política-piloto Aurora Tech. Dúvidas sobre a política devem ser encaminhadas ao RH Responde.",
                route, "TRH-04", True, "recusado_fora_escopo"
            )

        if route == "TRH-02" and any(term in clean.lower() for term in ("às vezes", "as vezes", "depende", "não sei", "nao sei")):
            step("data", "warning", "Função/contexto ambíguo; nenhuma elegibilidade presumida.")
            return finish("Informe sua função e se ela depende de atendimento presencial, laboratório ou manutenção física. Caso a política não cubra a situação, consulte o RH Responde.", route, "TRH-02", True, "perguntar_ambiguidade")
        if route == "TRH-02" and self._eligibility_data_missing(clean):
            step("data", "warning", "Função/contexto ausente; especialista não foi chamado.")
            return finish(
                "Para verificar a elegibilidade, informe sua função ou contexto de trabalho.",
                route, "TRH-02", True, "perguntar_dado_ausente"
            )

        step("data", "completed", "Dados suficientes para encaminhar ao especialista; exceções continuam sob decisão humana.")
        prompt = self.prompts.load(route, PROMPT_VERSIONS[route])
        step("prompt", "completed", f"Arquivo {route}_{PROMPT_VERSIONS[route]}.txt carregado.")
        context = self._context_for(route)
        step("context", "completed", f"Política autorizada do T2: {len(context)} caracteres. Sem histórico e sem documentos de uploads.")
        step("generation", "completed", "Prompt especialista enviado ao modelo.")
        answer = await generate([
            {"role": "system", "content": f"{prompt}\n\nBASE DE CONHECIMENTO:\n{context}"},
            {"role": "user", "content": clean},
        ], "validation", lambda raw: self._valid_specialist_output(route, raw))
        if answer is None:
            step("validation", "failed", "Falha técnica ou contrato inválido após o limite de repetição.")
            return finish("Não foi possível validar a resposta com segurança. Encaminhe a dúvida ao RH Responde.", route, route, False, "fallback_validacao")
        step("validation", "completed", "Campos obrigatórios e classificação verificados. Factualidade exige revisão humana.")
        return finish(answer.strip(), route, route, True, "respondido")

    def _context_for(self, route: Route) -> str:
        if route == "TRH-01":
            return self.knowledge_base
        keywords = ("eleg", "funç", "exceç", "remot", "dúvidas") if route == "TRH-02" else ("acesso", "autenticação", "dispositivo", "disponibilidade", "dúvidas", "incidente")
        sentences = re.split(r"(?<=[.!?])\s+", self.knowledge_base)
        return " ".join(sentence for sentence in sentences if any(word in sentence.lower() for word in keywords))

    @staticmethod
    def _parse_route(raw: str) -> Route | None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict) or set(data) != {"prompt_destino", "confianca", "motivo"}:
            return None
        route = data.get("prompt_destino")
        confidence = data.get("confianca")
        if not isinstance(route, str) or route not in {"TRH-01", "TRH-02", "TRH-03", "FORA_ESCOPO"}:
            return None
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
            return None
        if not isinstance(data["motivo"], str) or not data["motivo"].strip():
            return None
        return route

    @staticmethod
    def _valid_specialist_output(route: Route, raw: str) -> bool:
        required = ["Resposta:", "Regra aplicada:", "Próximo passo:"]
        if route == "TRH-02":
            required.insert(0, "Classificação:")
            match = re.search(r"Classificação:\s*(.+)", raw, re.IGNORECASE)
            if not match or match.group(1).strip().lower() not in {"elegível", "não elegível", "consultar rh"}:
                return False
        return all(re.search(rf"^{re.escape(label)}[ \t]*\S+", raw, re.IGNORECASE | re.MULTILINE) for label in required)

    @staticmethod
    def _eligibility_data_missing(question: str) -> bool:
        q = question.lower()
        asks_eligibility = any(term in q for term in ("elegível", "elegivel", "posso aderir", "posso trabalhar remot"))
        known_function = any(term in q for term in ("atendimento presencial", "laboratório", "laboratorio", "manutenção", "manutencao", "minha função", "minha funcao", "trabalho como", "trabalho em"))
        return asks_eligibility and not known_function
