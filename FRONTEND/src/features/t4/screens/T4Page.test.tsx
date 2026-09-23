import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { StrictMode } from 'react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getFlowConfig, runFlow } from '../services/t4Api';
import type { FlowResult } from '../utils/types';
import T4Page from './T4Page';

vi.mock('../services/t4Api', () => ({ getFlowConfig: vi.fn(), runFlow: vi.fn() }));
const result: FlowResult = {
  execution_id: 'run-1', executed_at: '2026-09-19T12:00:00Z', question: 'Quantos dias?', effective_question: 'Quantos dias?', correction_applied: false,
  answer: 'Resposta: Até dois dias.\nRegra aplicada: Até dois dias por semana.\nPróximo passo: Definir com o gestor.', route: 'TRH-01', prompt_id: 'TRH-01', prompt_version: 'v0.3',
  valid: true, retries: 0, latency_ms: 500, status: 'respondido', model: 'mistralai/mistral-large', temperature: 0.1, max_tokens: 500, mode: 'real', context: 'Política autorizada.',
  trace: [{ id: 'routing', state: 'completed', detail: 'TRH-04 → TRH-01' }], attempts: [{ phase: 'routing', output: '{}', error: '' }],
};

describe('Protótipo T4 integrado', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getFlowConfig).mockResolvedValue({ baseline_model: 'mistralai/mistral-large', model: 'mistralai/mistral-large', temperature: 0.1, max_tokens: 500, prompts: { 'TRH-01': 'v0.3', 'TRH-02': 'v0.1', 'TRH-03': 'v0.1', 'TRH-04': 'v0.1' }, knowledge_base: 'Política autorizada.', prompt_provenance: 'Reconstruídos; conferir originais.' });
    vi.mocked(runFlow).mockResolvedValue(result);
  });
  it('executa caso, mostra rastro e mantém revisão pendente', async () => {
    const user = userEvent.setup(); render(<T4Page />);
    await screen.findByText('mistralai/mistral-large');
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
  it('executa o modelo informado pelo backend sem impor Mistral', async () => {
    vi.mocked(getFlowConfig).mockResolvedValue({ model: 'openai/gpt-4o-mini', temperature: 0.1, max_tokens: 500, prompts: {}, knowledge_base: '', prompt_provenance: '' });
    const user = userEvent.setup(); render(<T4Page />);
    expect(await screen.findByText('openai/gpt-4o-mini')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Dias remotos' }));
    expect(screen.getByRole('button', { name: 'Executar fluxo →' })).toBeEnabled();
    await user.click(screen.getByRole('button', { name: 'Executar fluxo →' }));
    await waitFor(() => expect(runFlow).toHaveBeenCalledTimes(1));
  });
  it('não libera geração real sem confirmar a configuração', async () => {
    vi.mocked(getFlowConfig).mockRejectedValue(new Error('offline'));
    const user = userEvent.setup(); render(<T4Page />);
    await screen.findByText('Configuração indisponível');
    await user.click(screen.getByRole('button', { name: 'Dias remotos' }));
    expect(screen.getByRole('button', { name: 'Executar fluxo →' })).toBeDisabled();
    expect(runFlow).not.toHaveBeenCalled();
  });
  it('não dispara geração ao montar a página, mesmo em StrictMode', async () => {
    render(<StrictMode><T4Page /></StrictMode>);
    await screen.findByText('mistralai/mistral-large');
    expect(runFlow).not.toHaveBeenCalled();
  });
  it('bloqueia clique duplo e submits repetidos enquanto uma execução está pendente', async () => {
    let finish!: (value: FlowResult) => void;
    vi.mocked(runFlow).mockReturnValue(new Promise(resolve => { finish = resolve; }));
    const user = userEvent.setup(); render(<T4Page />);
    await screen.findByText('mistralai/mistral-large');
    await user.click(screen.getByRole('button', { name: 'Dias remotos' }));
    await user.dblClick(screen.getByRole('button', { name: 'Executar fluxo →' }));
    expect(screen.getByRole('button', { name: 'Executando fluxo…' })).toBeDisabled();
    const form = screen.getByLabelText('Pergunta ao copiloto').closest('form')!;
    fireEvent.submit(form);
    fireEvent.submit(form);
    expect(runFlow).toHaveBeenCalledTimes(1);
    await act(async () => finish(result));
    expect(await screen.findByRole('heading', { name: 'Resposta do copiloto' })).toBeInTheDocument();
    expect(runFlow).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: 'Executar fluxo →' })).toBeEnabled();
  });
  it('mostra diagnóstico de 429, origem e espera sem confundir limite com falta de saldo', async () => {
    vi.mocked(runFlow).mockResolvedValue({ ...result, valid: false, status: 'fallback_roteamento', retries: 1,
      attempts: [{ phase: 'routing', output: '', error: 'MODEL_RATE_LIMITED', retry_wait_seconds: 3,
        diagnostic: { http_status: 429, source: 'provider', reason: 'rate_limit', retry_after_seconds: 3,
          message: 'Limite de requisições atingido. Isso pode ocorrer mesmo com saldo disponível.' } }],
    });
    const user = userEvent.setup(); render(<T4Page />);
    await screen.findByText('mistralai/mistral-large');
    await user.click(screen.getByRole('button', { name: 'Dias remotos' }));
    await user.click(screen.getByRole('button', { name: 'Executar fluxo →' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('HTTP 429');
    expect(screen.getByRole('alert')).toHaveTextContent('mesmo com saldo disponível');
    await user.click(screen.getByText('Contexto e saídas brutas'));
    const diagnostic = screen.getByLabelText('Diagnóstico seguro do serviço');
    expect(diagnostic).toHaveTextContent('Origem: Provedor do modelo');
    expect(diagnostic).toHaveTextContent('Espera solicitada pelo serviço: 3 s');
    expect(diagnostic).toHaveTextContent('Espera aplicada antes da repetição: 3 s');
    expect(screen.getByText('Nenhum texto gerado nesta tentativa.')).toBeInTheDocument();
    expect(screen.queryByText('Sem resposta do provedor.')).not.toBeInTheDocument();
  });
  it('não inventa diagnóstico para execuções antigas sem os novos campos', async () => {
    vi.mocked(runFlow).mockResolvedValue({ ...result, valid: false, status: 'fallback_roteamento',
      attempts: [{ phase: 'routing', output: '', error: 'MODEL_RATE_LIMITED' }],
    });
    const user = userEvent.setup(); render(<T4Page />);
    await screen.findByText('mistralai/mistral-large');
    await user.click(screen.getByRole('button', { name: 'Dias remotos' }));
    await user.click(screen.getByRole('button', { name: 'Executar fluxo →' }));
    await screen.findByRole('heading', { name: 'Resposta do copiloto' });
    expect(screen.queryByLabelText('Diagnóstico seguro do serviço')).not.toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});
