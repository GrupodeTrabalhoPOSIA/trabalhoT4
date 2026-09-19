"""Auditoria com evidências sintéticas; não são resultados da campanha acadêmica."""
import copy
import hashlib
import io
import json
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.api.v1.routes import t6
from app.api.v1.routes.t4 import get_t4_service
from app.main import app
from app.models.final_delivery import DeliveryInput
from app.services import final_delivery as final
from app.services import final_package
from tests.test_t4_flow import service

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def state():
    cases = json.loads((ROOT / 'FRONTEND/src/features/t5/cases.json').read_text(encoding='utf-8'))
    fixtures = {c['fixture']: hashlib.sha256((ROOT / 'FRONTEND/public/entregas/t5' / c['fixture']).read_bytes()).hexdigest() for c in cases if c.get('fixture')}
    return {'frozen': True, 'drift': [], 'cases': cases, 'manifest': {'release_id': 't6-test', 'configuration': {'model': 'mistralai/mistral-large'}, 'fixtures': fixtures}, 'scenes': final.SCENES, 'risks': final.RISKS, 'review_case_ids': final.REVIEW_IDS}


def run_for(case, state, **changes):
    fixture = case.get('fixture')
    return {'execution_id': case['id'], 'executed_at': '2026-09-19T12:00:00Z', 'case_id': case['id'], 'release_id': 't6-test', 'candidate': 't5-v1', 'origin': 't6', 'mode': case['mode'], 'model': 'mistralai/mistral-large' if case['mode'] == 'real' else 'simulação determinística', 'question': case['question'], 'answer': 'Evidência sintética de teste unitário', 'status': 'respondido', 'valid': True, 'latency_ms': 1000, 'success': True, 'critical': False, 'configuration': state['manifest']['configuration'], 'sources': [{'document_hash': state['manifest']['fixtures'][fixture]}] if fixture else [], 'attempts': [{'phase': 'validation', 'output': 'resultado sintético'}], 'document': {'sha256': state['manifest']['fixtures'][fixture]} if fixture else None, **changes}


def complete_data(state):
    runs = [run_for(c, state) for c in state['cases']]
    for scene in final.SCENES:
        case = next(c for c in state['cases'] if c['id'] == scene['case_id'])
        runs.append(run_for(case, state, execution_id='smoke-' + scene['id'], purpose='smoke', scene_id=scene['id'], status=scene['statuses'][0]))
    reviews = [{'execution_id': c['id'], 'evaluator': person, 'scores': [5]*6 + [5 if c.get('fixture') else 0], 'notes': 'Justificativa sintética', 'recorded_at': '2026-09-19'} for c in state['cases'] if c['id'] in final.REVIEW_IDS for person in ['Pessoa A', 'Pessoa B']]
    risks = [{'id': r['id'], 'owner': 'Responsável de teste', 'controlled': True, 'notes': 'Verificado no cenário sintético', 'evidence_ids': r['cases']} for r in final.RISKS]
    return DeliveryInput(release_id='t6-test', runs=runs, reviews=reviews, risks=risks, decision={'choice': 'aprovado', 'responsible': 'Responsável de teste', 'rationale': 'Evidências sintéticas completas'}, regression_analysis='Comparação sintética para teste', retrospective='Manter, corrigir, priorizar, produção', contributions='Declaração sintética', demo_team='Operador e apresentador de teste', demo_minutes=10, rehearsal_notes='Ensaio sintético', contingency='Gravação identificada: exemplo de teste')


def test_empty_campaign_never_approves(state):
    report = final.audit(DeliveryInput(release_id='t6-test', decision={'choice': 'aprovado'}), state)
    assert report['recommendation'] == 'pendente' and not report['recorded']
    assert report['metrics']['success'] is None and report['metrics']['cost'] is None


def test_complete_campaign_and_two_independent_reviewers(state):
    data = complete_data(state)
    result = final.audit(data, state)
    assert result['ready'] and result['recorded'] and result['recommendation'] == 'aprovado'
    assert result['metrics']['count'] == 20 and result['reviewed_pairs'] == 10
    assert all(row['passed'] for row in result['smoke'])
    data.reviews[0].evaluator = 'Pessoa B'
    assert not final.audit(data, state)['recorded']


@pytest.mark.parametrize('field,value', [('release_id', None), ('configuration', {}), ('question', 'outra entrada'), ('model', 'outro-modelo'), ('mode', 'invalid_router')])
def test_incompatible_evidence_is_preserved_but_excluded(state, field, value):
    data = complete_data(state)
    setattr(data.runs[0], field, value)
    result = final.audit(data, state)
    assert result['metrics']['count'] == 19 and not result['recorded']
    assert result['excluded'][0]['execution_id'] == data.runs[0].execution_id


def test_wrong_fixture_and_smoke_do_not_replace_evaluation(state):
    data = complete_data(state)
    next(r for r in data.runs if r.case_id == 'M1').document = {'sha256': 'wrong'}
    result = final.audit(data, state)
    assert result['metrics']['count'] == 19 and not result['recorded']
    assert len(result['smoke']) == 6


def test_first_failure_cannot_be_hidden_by_retry_or_duplicate(state):
    data = complete_data(state)
    data.runs[0].success = False
    retry = data.runs[0].model_copy(update={'success': True})
    data.runs.append(retry)
    data.runs.append(retry.model_copy(update={'execution_id': 'retry'}))
    result = final.audit(data, state)
    assert result['rows'][0]['success'] is False and result['metrics']['success'] == 95
    assert len(result['excluded']) == 1
    data.runs[-1].critical = True
    assert final.audit(data, state)['recommendation'] == 'reprovado'


def test_uncontrolled_high_risk_blocks_approval(state):
    data = complete_data(state)
    data.risks[0].controlled = False
    result = final.audit(data, state)
    assert result['recommendation'] == 'reprovado' and not result['recorded']


def test_caveat_requires_condition_owner_and_future_deadline(state):
    data = complete_data(state)
    data.runs[0].latency_ms = 60000
    # Com 18 execuções reais, o p95 é a maior duração.
    data.decision.choice = 'aprovado com ressalvas'
    assert not final.audit(data, state)['recorded']
    data.decision.condition = 'Reduzir latência'
    data.decision.owner = 'Pessoa A'
    data.decision.deadline = (date.today() - timedelta(days=1)).isoformat()
    assert not final.audit(data, state)['recorded']
    data.decision.deadline = (date.today() + timedelta(days=7)).isoformat()
    assert final.audit(data, state)['recorded']


def test_cost_requires_complete_observations_and_candidate_origin(state):
    data = complete_data(state)
    real = [r for r in data.runs if r.mode == 'real' and r.purpose == 'evaluation']
    for run in real:
        run.cost_usd = .02
        run.cost_source = 'IDs das chamadas no registro do provedor'
        run.origin = 't5'
    result = final.audit(data, state)
    assert result['metrics']['cost'] == pytest.approx(.02)
    assert result['candidate_metrics']['count'] == 18
    real[0].cost_source = ''
    assert final.audit(data, state)['metrics']['cost'] is None


def test_runtime_detects_config_catalog_and_fixture_drift(state, tmp_path, monkeypatch):
    manifest = {**state['manifest'], 'files': {}, 'cases_sha256': final.digest(state['cases'])}
    manifest['release_id'] = 't6-' + final.digest({k: manifest[k] for k in ['files', 'configuration', 'cases_sha256', 'fixtures']})[:24]
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    (tmp_path / 'cases.json').write_text(json.dumps(state['cases']), encoding='utf-8')
    (tmp_path / 'fixtures').mkdir()
    for name in manifest['fixtures']:
        (tmp_path / 'fixtures' / name).write_bytes((ROOT / 'FRONTEND/public/entregas/t5' / name).read_bytes())
    monkeypatch.setattr(final, 'RELEASE_ROOT', tmp_path)
    monkeypatch.setattr(final, 'runtime_configuration', lambda: manifest['configuration'])
    assert final.release_state()['frozen']
    (tmp_path / 'cases.json').write_text('[]')
    assert 'Conjunto de testes divergente.' in final.release_state()['drift']
    monkeypatch.setattr(final, 'runtime_configuration', lambda: {})
    (tmp_path / 'fixtures' / next(iter(manifest['fixtures']))).write_bytes(b'changed')
    assert len(final.release_state()['drift']) == 3


def test_api_rejects_wrong_version_and_executes_controlled_failure(state, monkeypatch):
    monkeypatch.setattr(t6, 'release_state', lambda: state)
    flow = service([])
    app.dependency_overrides[get_t4_service] = lambda: flow
    try:
        client = TestClient(app)
        assert client.post('/api/v1/t6/run', json={'case_id': 'E2', 'release_id': 'old'}).status_code == 409
        assert client.post('/api/v1/t6/run', json={'case_id': 'E2', 'release_id': 't6-test', 'purpose': 'smoke', 'scene_id': 'principal'}).status_code == 422
        response = client.post('/api/v1/t6/run', json={'case_id': 'E2', 'release_id': 't6-test', 'purpose': 'smoke', 'scene_id': 'falha'})
        assert response.status_code == 200
        run = response.json()
        assert run['status'] == 'fallback_validacao' and run['origin'] == 't6'
        assert run['release_id'] == 't6-test' and run['success'] is None
        assert not flow.llm_client.calls
    finally:
        app.dependency_overrides.clear()


def test_draft_package_is_readable_and_preserves_pending_state():
    state = final.release_state()
    # Congelar após alterações antes de executar este teste de artefato.
    data = DeliveryInput(release_id=state['manifest']['release_id'])
    report = final.audit(data, state)
    content = final_package.build_package(data, report, state)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert 'RASCUNHO' in archive.read('STATUS.md').decode()
        assert 'architecture/arquitetura.svg' in archive.namelist()
        assert any(n.startswith('prompts/') for n in archive.namelist())
        assert json.loads(archive.read('evaluation/final/gate.json'))['decision'] == 'pendente'
        with pymupdf.open(stream=archive.read('apresentacao.pdf'), filetype='pdf') as pdf:
            assert len(pdf) == 10
            assert all(len(page.get_text()) > 100 for page in pdf)
            assert 'PENDENTE' in pdf[0].get_text()
        with zipfile.ZipFile(io.BytesIO(archive.read('release/source.zip'))) as source:
            assert not any(Path(n).name == '.env' or '/.venv/' in n or '/node_modules/' in n for n in source.namelist())
            assert 'BACKEND/evaluation/freeze_final.py' in source.namelist()
