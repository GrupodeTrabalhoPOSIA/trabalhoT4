"""Contratos T5 e isolamento documental; nenhum teste faz chamadas externas."""
from pathlib import Path
import json
from unittest.mock import Mock

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import t5
from app.api.v1.routes.t4 import get_t4_service
from app.main import app
from tests.test_t4_flow import service

ROUTE = '{"prompt_destino":"TRH-01","confianca":0.98,"motivo":"regra"}'
ANSWER = "Resposta: Dois dias.\nRegra aplicada: Fonte anexo; dois dias.\nPróximo passo: Consultar RH."
FIXTURES = Path(__file__).resolve().parents[2] / "FRONTEND/public/entregas/t5"


@pytest.fixture
def client(monkeypatch):
    flow = service([ROUTE, ANSWER])
    app.dependency_overrides[get_t4_service] = lambda: flow
    embed = Mock()
    embed.embed_documents.side_effect = lambda texts: [[1., 0.] for _ in texts]
    embed.embed_query.return_value = [1., 0.]
    monkeypatch.setattr(t5, "get_embedding_service", lambda: embed)
    yield TestClient(app), flow, embed
    app.dependency_overrides.clear()


def test_document_reuses_specialist_without_promoting_document_to_system(client):
    http, flow, embed = client
    content = (FIXTURES / "injecao-v1.pdf").read_bytes()
    result = http.post('/api/v1/t5/run', data={"question": "Quantos dias?"}, files={"file": ("injecao-v1.pdf", content, "application/pdf")}).json()
    assert result['status'] == 'respondido' and result['valid']
    assert result['sources'][0]['page'] == 1
    assert len(result['document']['sha256']) == 64
    assert result['configuration']['model'] == 'mistralai/mistral-large'
    messages = flow.llm_client.calls[-1]
    assert "COMANDO MALICIOSO" not in messages[0]['content']
    assert "COMANDO MALICIOSO" in json.loads(messages[1]['content'])['trechos']
    assert "BASE DE CONHECIMENTO — política-piloto" not in messages[0]['content']
    assert embed.embed_documents.call_count == 1


def test_no_retrieval_evidence_does_not_call_llm(client):
    http, flow, embed = client
    embed.embed_query.return_value = [-1., 0.]
    result = http.post('/api/v1/t5/run', data={"question": "Benefício desconhecido?"}, files={"file": ("politica-v1.pdf", (FIXTURES / "politica-v1.pdf").read_bytes(), "application/pdf")}).json()
    assert result['status'] == 'sem_evidencia'
    assert result['sources'] == [] and flow.llm_client.calls == []


@pytest.mark.parametrize(('name', 'content', 'mime', 'code'), [
    ('teste.exe', b'not allowed', 'application/octet-stream', 'UNSUPPORTED_FILE_TYPE'),
    ('teste.pdf', b'broken pdf', 'application/pdf', 'INVALID_PDF'),
    ('teste.txt', b'curto', 'text/plain', 'LOW_QUALITY'),
    ('teste.txt', b'', 'text/plain', 'EMPTY_FILE'),
    ('teste.txt', b'x' * (10 * 1024 * 1024 + 1), 'text/plain', 'FILE_TOO_LARGE'),
], ids=['unsupported', 'corrupt-pdf', 'short-text', 'empty', 'oversized'])
def test_rejected_input_is_evidence_without_provider_calls(client, name, content, mime, code):
    http, flow, embed = client
    response = http.post('/api/v1/t5/run', data={"question": "Quantos dias?"}, files={"file": (name, content, mime)})
    assert response.status_code == 200
    assert response.json()['error_code'] == code
    assert response.json()['status'] == 'entrada_rejeitada'
    assert response.json()['execution_id']
    assert flow.llm_client.calls == [] and not embed.embed_documents.called


def test_pdf_without_text_and_page_limit(client):
    http, flow, embed = client
    blank = (FIXTURES / "sem-texto-v1.pdf").read_bytes()
    assert http.post('/api/v1/t5/run', data={"question": "Quantos dias?"}, files={"file": ('blank.pdf', blank, 'application/pdf')}).json()['error_code'] == 'EMPTY_DOCUMENT'
    with pymupdf.open() as doc:
        for _ in range(21):
            doc.new_page()
        large = doc.tobytes()
    assert http.post('/api/v1/t5/run', data={"question": "Quantos dias?"}, files={"file": ('long.pdf', large, 'application/pdf')}).json()['error_code'] == 'PAGE_LIMIT'
    assert not embed.embed_documents.called and not flow.llm_client.calls


def test_text_mode_and_simulation_remain_available(client):
    http, flow, embed = client
    result = http.post('/api/v1/t5/run', data={"question": "Quantos dias?"}).json()
    assert result['status'] == 'respondido' and result['document'] is None
    assert 'BASE DE CONHECIMENTO' in flow.llm_client.calls[-1][0]['content']
    simulation = http.post('/api/v1/t5/run', data={"question": "Simular", "mode": "invalid_specialist"}).json()
    assert simulation['status'] == 'fallback_validacao' and simulation['retries'] == 1
    assert simulation['model'] == 'simulação determinística'
    assert not embed.embed_documents.called


def test_invalid_requests_and_safe_config(client):
    http, _, _ = client
    assert http.post('/api/v1/t5/run', data={"question": "   "}).status_code == 422
    assert http.post('/api/v1/t5/run', data={"question": "x", "mode": "unexpected"}).status_code == 422
    assert http.post('/api/v1/t5/run', data={"question": "x", "mode": "invalid_router"}, files={"file": ('x.txt', b'text', 'text/plain')}).status_code == 422
    config = http.get('/api/v1/t5/config')
    assert config.json()['candidate'] == 't5-v1'
    assert 'api_key' not in config.text and 'postgresql://' not in config.text
