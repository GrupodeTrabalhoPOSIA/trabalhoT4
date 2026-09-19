"""Contratos do protótipo web; nenhum teste chama o provedor real."""
import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes.t4 import get_t4_service
from app.core.errors import AppError
from app.main import app
from tests.test_t4_flow import service


@pytest.mark.parametrize("raw", ['[]', 'null', 'true', '{"prompt_destino":[],"confianca":1,"motivo":"x"}', '{"prompt_destino":"TRH-01","confianca":true,"motivo":"x"}', '{"prompt_destino":"TRH-01","confianca":0.9}'])
def test_invalid_router_contract_falls_back_without_crashing(raw):
    flow = service([raw, raw])
    result = asyncio.run(flow.run("Pergunta"))
    assert result.status == "fallback_roteamento"
    assert not result.valid and result.retries == 1
    assert len(flow.llm_client.calls) == 2


def test_low_confidence_asks_without_calling_specialist():
    flow = service(['{"prompt_destino":"TRH-02","confianca":0.4,"motivo":"incerto"}'])
    result = asyncio.run(flow.run("Pode ser?"))
    assert result.status == "perguntar_ambiguidade"
    assert len(flow.llm_client.calls) == 1


def test_retry_budget_shared_by_router_and_specialist():
    flow = service(['invalido', '{"prompt_destino":"TRH-01","confianca":0.9,"motivo":"regra"}', 'inválido'])
    result = asyncio.run(flow.run("Quantos dias?"))
    assert result.status == "fallback_validacao" and result.retries == 1
    assert len(flow.llm_client.calls) == 3


def test_empty_field_is_not_filled_by_the_next_line_label():
    flow = service([])
    assert not flow._valid_specialist_output("TRH-01", "Resposta:\nRegra aplicada: Até dois dias.\nPróximo passo: Consulte RH.")


def test_timeout_retries_once_and_returns_safe_result():
    class TimeoutClient:
        calls = 0
        async def complete(self, messages):
            self.calls += 1
            raise AppError(status_code=504, code="MODEL_TIMEOUT", message="segredo não deve aparecer")
    flow = service([])
    flow.llm_client = TimeoutClient()
    result = asyncio.run(flow.run("Quantos dias?"))
    assert result.retries == 1 and result.status == "fallback_roteamento"
    assert flow.llm_client.calls == 2
    assert "segredo" not in str(result)
    assert result.attempts[0]["error"] == "MODEL_TIMEOUT"


def test_correction_replaces_original_and_context_is_selected():
    flow = service(['{"prompt_destino":"TRH-03","confianca":0.9,"motivo":"segurança"}', 'Resposta: Use MFA.\nRegra aplicada: O acesso requer autenticação multifator e dispositivo gerenciado.\nPróximo passo: Use dispositivo gerenciado.'])
    app.dependency_overrides[get_t4_service] = lambda: flow
    try:
        response = TestClient(app).post('/api/v1/t4/run', json={"question": "Qual o cardápio?", "correction": "Como acessar documentos?"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body['correction_applied'] and body['effective_question'] == "Como acessar documentos?"
    assert body['route'] == 'TRH-03' and body['trace'] and body['attempts']
    assert "cardápio" not in json.dumps(flow.llm_client.calls, ensure_ascii=False)
    assert "Internet e energia" not in body['context']
    assert "dispositivo gerenciado" in body['context']


@pytest.mark.parametrize(('mode', 'status', 'valid'), [('invalid_router', 'respondido', True), ('invalid_specialist', 'fallback_validacao', False)])
def test_simulation_uses_real_orchestration_without_provider(mode, status, valid):
    body = TestClient(app).post('/api/v1/t4/run', json={"question": "Simular", "mode": mode}).json()
    assert body['mode'] == mode and body['model'] == 'simulação determinística'
    assert body['status'] == status and body['valid'] == valid
    assert body['retries'] == 1 and len(body['attempts']) == 3


def test_public_config_loads_templates_and_never_exposes_credentials():
    response = TestClient(app).get('/api/v1/t4/config')
    assert response.status_code == 200
    body = response.json()
    assert len(body['prompts']) == 4 and 'política-piloto' in body['knowledge_base']
    assert 'api_key' not in response.text and 'postgresql://' not in response.text


def test_request_rejects_blank_question_and_unknown_simulation():
    client = TestClient(app)
    assert client.post('/api/v1/t4/run', json={"question": "  "}).status_code == 422
    assert client.post('/api/v1/t4/run', json={"question": "teste", "mode": "arbitrary"}).status_code == 422
