import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { apiRequest } from '@/services/apiClient';
import { cases } from '@/features/t5/data';
import T6Page from './T6Page';
import manifest from './releaseManifest.json';
import { emptyDelivery, mergeEvidence, parseEvidence } from './evidence';

vi.mock('@/services/apiClient', () => ({ apiRequest: vi.fn(), ApiError: class extends Error {} }));
const report = { ready: false, recorded: false, recommendation: 'pendente', issues: ['20 casos sem execução válida'], metrics: { count: 0, reviewed: 0, success: null, format: null, source: null, p95: null, cost: null }, groups: {}, reviewed_pairs: 0, rubric: [], rows: [], smoke: [], excluded: [], risk_checks: [], regressions: [] };
const state = { frozen: true, drift: [], manifest, cases, scenes: [], risks: [], review_case_ids: [] };
const evidence = { execution_id: 'test-1', executed_at: '2026-09-19', case_id: 'P1', candidate: 't5-v1', mode: 'real', model: 'mistralai/mistral-large', question: 'Pergunta sintética', answer: 'Saída sintética', status: 'respondido', valid: true, latency_ms: 1000, success: false, critical: false, sources: [], attempts: [], release_id: 'versao-antiga' };

describe('Entrega final', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    vi.mocked(apiRequest).mockImplementation(async path => (path === '/t6/manifest' ? state : report) as never);
  });
  it('exibe versão conferida e mantém gate pendente antes da avaliação', async () => {
    const user = userEvent.setup();
    render(<T6Page />);
    expect(await screen.findByRole('heading', { name: 'Versão conferida com o backend' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /Avaliação final/ }));
    expect(screen.getAllByRole('button', { name: /^Executar [A-Z][0-9]$/ })).toHaveLength(20);
    await user.click(screen.getByRole('button', { name: /Gate e riscos/ }));
    expect(await screen.findByRole('heading', { name: 'PENDENTE' })).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText('Decisão do responsável'), 'aprovado');
    expect(screen.getByText(/Decisão ainda não validada/)).toBeInTheDocument();
  });
  it('bloqueia execução e pacote quando as versões divergem', async () => {
    vi.mocked(apiRequest).mockImplementation(async path => (path === '/t6/manifest' ? { ...state, manifest: { ...manifest, release_id: 'outra-versao' } } : report) as never);
    const user = userEvent.setup(); render(<T6Page />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Frontend e backend precisam usar a mesma versão');
    await user.click(screen.getByRole('button', { name: /Pacote final/ }));
    expect(screen.getByRole('button', { name: /Baixar pacote ZIP/ })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: /Avaliação final/ }));
    expect(screen.getByRole('button', { name: 'Executar P1' })).toBeDisabled();
  });
  it('salva formulários como rascunho e restaura após remontagem', async () => {
    const user = userEvent.setup(); const view = render(<T6Page />);
    await user.click(screen.getByRole('button', { name: /Pacote final/ }));
    fireEvent.change(screen.getByLabelText('Contribuições dos integrantes'), { target: { value: 'Contribuição declarada para teste de persistência' } });
    await waitFor(() => expect(localStorage.getItem('aurora.final-delivery.v1')).toContain('teste de persistência'));
    view.unmount(); render(<T6Page />);
    await user.click(screen.getByRole('button', { name: /Pacote final/ }));
    expect(screen.getByLabelText('Contribuições dos integrantes')).toHaveValue('Contribuição declarada para teste de persistência');
  });
  it('preserva hashes antigos e não sobrescreve uma falha ao mesclar JSON', () => {
    const existing = parseEvidence(JSON.stringify({ runs: [evidence], reviews: [] }), manifest.release_id);
    const incoming = parseEvidence(JSON.stringify({ runs: [{ ...evidence, success: true }], reviews: [] }), manifest.release_id);
    const merged = mergeEvidence(existing, incoming);
    expect(merged.runs).toHaveLength(1);
    expect(merged.runs[0].success).toBe(false);
    expect(merged.runs[0].release_id).toBe('versao-antiga');
    expect(() => parseEvidence('{"runs":[{}],"reviews":[]}', manifest.release_id)).toThrow('inválido');
    expect(emptyDelivery(manifest.release_id).decision.choice).toBe('pendente');
  });
});
