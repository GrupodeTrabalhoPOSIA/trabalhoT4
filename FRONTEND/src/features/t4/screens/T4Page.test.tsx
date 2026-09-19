import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getFlowConfig, runFlow } from '../services/t4Api';
import type { FlowResult } from '../utils/types';
import T4Page from './T4Page';

vi.mock('../services/t4Api', () => ({ getFlowConfig: vi.fn(), runFlow: vi.fn() }));
const result: FlowResult = {
  execution_id: 'run-1', executed_at: '2026-09-19T12:00:00Z', question: 'Quantos dias?', effective_question: 'Quantos dias?', correction_applied: false,
  answer: 'Resposta: Até dois dias.\nRegra aplicada: Até dois dias por semana.\nPróximo passo: Definir com o gestor.', route: 'TRH-01', prompt_id: 'TRH-01', prompt_version: 'v0.3',
  valid: true, retries: 0, latency_ms: 500, status: 'respondido', model: 'modelo-teste', temperature: 0.1, max_tokens: 500, mode: 'real', context: 'Política autorizada.',
  trace: [{ id: 'routing', state: 'completed', detail: 'TRH-04 → TRH-01' }], attempts: [{ phase: 'routing', output: '{}', error: '' }],
};

describe('Protótipo T4 integrado', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getFlowConfig).mockResolvedValue({ model: 'modelo-teste', temperature: 0.1, max_tokens: 500, prompts: { 'TRH-01': 'v0.3', 'TRH-02': 'v0.1', 'TRH-03': 'v0.1', 'TRH-04': 'v0.1' }, knowledge_base: 'Política autorizada.', prompt_provenance: 'Reconstruídos; conferir originais.' });
    vi.mocked(runFlow).mockResolvedValue(result);
  });
  it('executa caso, mostra rastro e mantém revisão pendente', async () => {
    const user = userEvent.setup(); render(<T4Page />);
    await screen.findByText('modelo-teste');
    await user.click(screen.getByRole('button', { name: 'Dias remotos' }));
    await user.click(screen.getByRole('button', { name: 'Executar fluxo →' }));
    expect(await screen.findByRole('heading', { name: 'Resposta do copiloto' })).toBeInTheDocument();
    expect(runFlow).toHaveBeenCalledWith(expect.objectContaining({ mode: 'real', correction: '' }), expect.any(AbortSignal));
    expect(screen.getByText('TRH-04 → TRH-01')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Registrar avaliação humana'));
    expect(screen.getByLabelText('Sem informação inventada?')).toHaveValue('');
    await user.click(screen.getByRole('button', { name: /Testes e evidências/ }));
    expect(screen.getByText(/1 de 13 casos/)).toBeInTheDocument();
    const baseline = screen.getByRole('table', { name: /Mesmas métricas/ });
    expect(within(baseline).getAllByText('Pendente')).toHaveLength(5);
  });
  it('identifica erro simulado no payload e na interface', async () => {
    const user = userEvent.setup(); render(<T4Page />);
    await user.click(screen.getByRole('button', { name: /Testes e evidências/ }));
    await user.click(screen.getByRole('button', { name: 'Carregar E1 →' }));
    expect(screen.getByText(/Simulação determinística de falha/)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Executar simulação →' }));
    await waitFor(() => expect(runFlow).toHaveBeenCalledWith(expect.objectContaining({ mode: 'invalid_router' }), expect.any(AbortSignal)));
  });
  it('envia correção explícita sem reaproveitar histórico', async () => {
    const user = userEvent.setup(); render(<T4Page />);
    await user.click(screen.getByRole('button', { name: 'Dias remotos' }));
    await user.click(screen.getByRole('button', { name: 'Executar fluxo →' }));
    await screen.findByRole('heading', { name: 'Resposta do copiloto' });
    await user.click(screen.getByRole('button', { name: /Corrigir ou complementar/ }));
    await user.type(screen.getByLabelText('Pergunta corrigida ou complementada'), 'Trabalho em laboratório. Sou elegível?');
    await user.click(screen.getByRole('button', { name: 'Executar fluxo →' }));
    expect(vi.mocked(runFlow).mock.calls[1][0]).toEqual({ question: 'Quantos dias?', correction: 'Trabalho em laboratório. Sou elegível?', mode: 'real' });
  });
  it('mostra falha de rede sem inventar uma execução concluída', async () => {
    vi.mocked(runFlow).mockRejectedValue(new TypeError('Failed to fetch'));
    const user = userEvent.setup(); render(<T4Page />);
    await user.click(screen.getByRole('button', { name: 'Dias remotos' }));
    await user.click(screen.getByRole('button', { name: 'Executar fluxo →' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Não foi possível acessar');
    expect(screen.getByText('0 / 13 casos executados')).toBeInTheDocument();
  });
});
