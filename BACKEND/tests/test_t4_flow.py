from pathlib import Path
import asyncio
from unittest.mock import AsyncMock

import pytest

from app.core.errors import AppError
from app.models.errors import ProviderDiagnostic
from app.services.t4 import PromptRegistry, T4FlowService

PROMPTS = Path(__file__).parents[1] / "prompts" / "templates"
KB = (Path(__file__).parents[1] / "knowledge" / "politica_aurora_tech.txt").read_text(encoding="utf-8")

class ScriptedLLM:
    def __init__(self, outputs): self.outputs=list(outputs); self.calls=[]
    async def complete(self, messages):
        self.calls.append(messages)
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return output

def service(outputs): return T4FlowService(llm_client=ScriptedLLM(outputs), prompt_registry=PromptRegistry(PROMPTS), knowledge_base=KB)

def test_routes_rule_and_validates_output():
    s=service(['{"prompt_destino":"TRH-01","confianca":0.98,"motivo":"regra"}', 'Resposta: Até dois dias.\nRegra aplicada: Colaboradores elegíveis poderão trabalhar remotamente até dois dias por semana.\nPróximo passo: Definir os dias com o gestor.'])
    r=asyncio.run(s.run('Quantos dias posso trabalhar remotamente?'))
    assert (r.route,r.prompt_id,r.valid,r.retries,r.status)==('TRH-01','TRH-01',True,0,'respondido')

def test_missing_eligibility_data_asks_user_without_specialist_call():
    s=service(['{"prompt_destino":"TRH-02","confianca":0.95,"motivo":"elegibilidade"}'])
    r=asyncio.run(s.run('Sou elegível ao trabalho híbrido?'))
    assert r.status=='perguntar_dado_ausente' and r.prompt_id=='TRH-02'

def test_out_of_scope_is_safely_refused():
    s=service(['{"prompt_destino":"FORA_ESCOPO","confianca":0.99,"motivo":"fora"}'])
    r=asyncio.run(s.run('Qual é o cardápio do refeitório?'))
    assert r.status=='recusado_fora_escopo'

def test_router_invalid_json_retries_once():
    s=service(['não é json','{"prompt_destino":"TRH-03","confianca":0.9,"motivo":"segurança"}', 'Resposta: Use autenticação multifator.\nRegra aplicada: O acesso requer autenticação multifator e dispositivo gerenciado.\nPróximo passo: Usar dispositivo gerenciado.'])
    r=asyncio.run(s.run('Como devo acessar os documentos?'))
    assert r.route=='TRH-03' and r.retries==1 and r.valid

def test_specialist_invalid_format_retries_once():
    s=service(['{"prompt_destino":"TRH-01","confianca":0.9,"motivo":"regra"}', 'Até dois dias.', 'Resposta: Até dois dias.\nRegra aplicada: Até dois dias por semana.\nPróximo passo: Definir com o gestor.'])
    r=asyncio.run(s.run('Quantos dias remotos?'))
    assert r.retries==1 and r.valid

def test_second_invalid_specialist_output_uses_fallback():
    s=service(['{"prompt_destino":"TRH-03","confianca":0.9,"motivo":"segurança"}', 'inválida', 'ainda inválida'])
    r=asyncio.run(s.run('Como acesso os documentos?'))
    assert not r.valid and r.status=='fallback_validacao'


ROUTE = '{"prompt_destino":"TRH-01","confianca":0.98,"motivo":"regra"}'
ANSWER = 'Resposta: Até dois dias.\nRegra aplicada: Até dois dias por semana.\nPróximo passo: Definir com o gestor.'


@pytest.mark.parametrize("wrapper", ["{}", "```json\n{}\n```", "```\n{}\n```", " \r\n```JSON\r\n{}\r\n```\r\n "])
def test_json_route_reaches_specialist_without_retry_and_preserves_raw_output(wrapper):
    raw = wrapper.format(ROUTE)
    flow = service([raw, ANSWER])
    result = asyncio.run(flow.run("Quantos dias por semana posso trabalhar remotamente?"))
    assert result.valid and result.status == "respondido"
    assert result.route == "TRH-01" and result.retries == 0
    assert len(flow.llm_client.calls) == 2
    assert result.attempts[0] == {"phase": "routing", "output": raw, "error": ""}


@pytest.mark.parametrize("raw", [
    "Texto antes\n```json\n" + ROUTE + "\n```",
    "```json\n" + ROUTE + "\n```\nTexto depois",
    "```json\n" + ROUTE + "\n```\n```json\n" + ROUTE + "\n```",
    "```python\n" + ROUTE + "\n```",
    "```json\n" + ROUTE,
    '```json\n{"prompt_destino":"TRH-99","confianca":0.95,"motivo":"regra"}\n```',
    '```json\n{"prompt_destino":"TRH-01","confianca":true,"motivo":"regra"}\n```',
    '```json\n{"prompt_destino":"TRH-01","confianca":0.95}\n```',
    '```json\n{"prompt_destino":"TRH-01","confianca":0.95,"motivo":"regra","extra":1}\n```',
    '```json\n{"prompt_destino":"TRH-01","confianca":0.95,"motivo":"regra",}\n```',
])
def test_invalid_wrapped_route_still_falls_back_after_one_retry(raw):
    flow = service([raw, raw])
    result = asyncio.run(flow.run("Quantos dias remotos?"))
    assert not result.valid and result.status == "fallback_roteamento"
    assert result.retries == 1 and len(flow.llm_client.calls) == 2
    assert all(attempt["error"] == "INVALID_FORMAT" for attempt in result.attempts)


def test_fenced_low_confidence_keeps_clarification_without_specialist():
    flow = service(['```json\n' + ROUTE.replace('0.98', '0.5') + '\n```'])
    result = asyncio.run(flow.run("Pode explicar?"))
    assert result.status == "perguntar_ambiguidade" and result.retries == 0
    assert len(flow.llm_client.calls) == 1


def rate_limit(wait=None):
    return AppError(status_code=502, code="MODEL_RATE_LIMITED", message="privado", diagnostic=ProviderDiagnostic(
        http_status=429, source="provider", reason="rate_limit", retry_after_seconds=wait,
    ))


@pytest.mark.parametrize(("wait", "expected_wait"), [(None, 2), (0, 0), (3, 3), (30, 30)])
def test_rate_limit_waits_once_then_recovers_without_changing_prompts(monkeypatch, wait, expected_wait):
    sleep = AsyncMock()
    monkeypatch.setattr("app.services.t4.flow.asyncio.sleep", sleep)
    flow = service([rate_limit(wait), ROUTE, ANSWER])
    result = asyncio.run(flow.run("Quantos dias?"))
    assert result.valid and result.retries == 1
    assert len(flow.llm_client.calls) == 3
    assert flow.llm_client.calls[0] == flow.llm_client.calls[1]
    sleep.assert_awaited_once_with(expected_wait)
    assert result.attempts[0]["retry_wait_seconds"] == expected_wait
    assert result.attempts[0]["diagnostic"]["http_status"] == 429
    assert "privado" not in str(result)


def test_specialist_can_use_the_same_global_retry_budget(monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr("app.services.t4.flow.asyncio.sleep", sleep)
    flow = service([ROUTE, rate_limit(4), ANSWER])
    result = asyncio.run(flow.run("Quantos dias?"))
    assert result.valid and result.retries == 1
    assert flow.llm_client.calls[1] == flow.llm_client.calls[2]
    sleep.assert_awaited_once_with(4)


def test_repeated_rate_limit_stops_without_sleeping_or_calling_again(monkeypatch):
    sleep = AsyncMock()
    monkeypatch.setattr("app.services.t4.flow.asyncio.sleep", sleep)
    flow = service([rate_limit(2), rate_limit(5)])
    result = asyncio.run(flow.run("Quantos dias?"))
    assert not result.valid and result.retries == 1
    assert len(flow.llm_client.calls) == 2
    sleep.assert_awaited_once_with(2)
    assert result.attempts[-1]["diagnostic"]["retry_after_seconds"] == 5
    assert "retry_wait_seconds" not in result.attempts[-1]


@pytest.mark.parametrize("wait", [31, 300, 86400])
def test_long_wait_is_reported_without_premature_retry(monkeypatch, wait):
    sleep = AsyncMock()
    monkeypatch.setattr("app.services.t4.flow.asyncio.sleep", sleep)
    flow = service([rate_limit(wait)])
    result = asyncio.run(flow.run("Quantos dias?"))
    assert result.retries == 0 and not result.valid
    assert len(flow.llm_client.calls) == 1
    sleep.assert_not_awaited()
    assert any(f"espera de {wait} s" in step["detail"] for step in result.trace)


@pytest.mark.parametrize("outputs", [
    ["inválido", ROUTE, rate_limit(2)],
    [rate_limit(2), ROUTE, "inválido"],
])
def test_retry_budget_is_shared_between_format_and_rate_limits(monkeypatch, outputs):
    sleep = AsyncMock()
    monkeypatch.setattr("app.services.t4.flow.asyncio.sleep", sleep)
    flow = service(outputs)
    result = asyncio.run(flow.run("Quantos dias?"))
    assert result.retries == 1 and result.status == "fallback_validacao"
    assert len(flow.llm_client.calls) == 3
    assert sleep.await_count == (1 if isinstance(outputs[0], AppError) else 0)


@pytest.mark.parametrize("code", ["MODEL_AUTH_ERROR", "MODEL_CREDIT_LIMIT", "MODEL_NOT_CONFIGURED"])
def test_permanent_errors_do_not_retry(monkeypatch, code):
    sleep = AsyncMock()
    monkeypatch.setattr("app.services.t4.flow.asyncio.sleep", sleep)
    flow = service([AppError(status_code=502, code=code, message="segredo")])
    result = asyncio.run(flow.run("Quantos dias?"))
    assert not result.valid and result.retries == 0
    assert len(flow.llm_client.calls) == 1
    assert "segredo" not in str(result)
    sleep.assert_not_awaited()


def test_cancellation_during_wait_does_not_issue_another_paid_call(monkeypatch):
    sleep = AsyncMock(side_effect=asyncio.CancelledError)
    monkeypatch.setattr("app.services.t4.flow.asyncio.sleep", sleep)
    flow = service([rate_limit(3)])
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(flow.run("Quantos dias?"))
    assert len(flow.llm_client.calls) == 1
