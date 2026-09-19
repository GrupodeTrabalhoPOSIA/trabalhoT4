import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import T5Page from './T5Page';
import { apiRequest } from '@/services/apiClient';

vi.mock('@/services/apiClient', () => ({ apiRequest: vi.fn(), ApiError: class extends Error {} }));
const config = { candidate: 't5-v1', model: 'mistralai/mistral-large' };
const result = { execution_id: 'run-1', executed_at: '2026-09-19T12:00:00Z', candidate: 't5-v1', question: 'Pergunta livre', mode: 'real', model: 'mistralai/mistral-large', answer: 'Resposta: Dois dias.', route: 'TRH-01', prompt_id: 'TRH-01', prompt_version: 'v0.3', valid: true, retries: 0, latency_ms: 1000, status: 'respondido', trace: [], attempts: [], context: '', sources: [], document: null, error_code: null };
describe('Página do Trabalho 5', () => {
  beforeEach(() => { vi.clearAllMocks(); vi.mocked(apiRequest).mockResolvedValue(config); });
  it('envia pergunta e arquivo reais e mantém a revisão pendente', async () => {
    const user = userEvent.setup();
    render(<T5Page />);
    await waitFor(() => expect(apiRequest).toHaveBeenCalledWith('/t5/config', expect.anything()));
    const file = new File(['Política sintética com regras de trabalho híbrido.'], 'politica.txt', { type: 'text/plain' });
    await user.upload(screen.getByLabelText('Anexar política corporativa'), file);
    fireEvent.change(screen.getByLabelText('Pergunta sobre a política'), { target: { value: 'Quantos dias?' } });
    vi.mocked(apiRequest).mockResolvedValueOnce(result);
    await user.click(screen.getByRole('button', { name: /Consultar política/ }));
    expect(await screen.findByRole('heading', { name: 'Resposta e fundamentação' })).toBeInTheDocument();
    const options = vi.mocked(apiRequest).mock.calls.at(-1)?.[1];
    expect((options?.body as FormData).get('file')).toBe(file);
    expect((options?.body as FormData).get('question')).toBe('Quantos dias?');
    expect(screen.getByLabelText('Atendeu ao resultado esperado?')).toHaveValue('');
    await user.click(screen.getByRole('button', { name: /Riscos e entrega/ }));
    expect(screen.getByRole('button', { name: /Exportar decisão/ })).toBeDisabled();
  });
  it('apresenta o catálogo e o plano mesmo sem API', async () => {
    vi.mocked(apiRequest).mockRejectedValueOnce(new Error('offline'));
    const user = userEvent.setup(); render(<T5Page />);
    expect(await screen.findByText(/configuração do Trabalho 5 está indisponível/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Consultar política/ })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: /Testes e evidências/ }));
    expect(screen.getAllByRole('button', { name: /^Carregar / })).toHaveLength(20);
    await user.click(screen.getByRole('button', { name: /Métricas e rubrica/ }));
    expect(screen.getByRole('heading', { name: 'Rubrica de avaliação independente' })).toBeInTheDocument();
  });
  it('prepara a fixture do caso e ao editar a pergunta remove sua identificação', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(new Blob(['%PDF-fixture'], { type: 'application/pdf' }), { headers: { 'content-type': 'application/pdf' } })));
    const user = userEvent.setup(); render(<T5Page />);
    await user.click(screen.getByRole('button', { name: /Experimentar PDF/ }));
    expect(await screen.findByText('M1 · Representativo')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Pergunta sobre a política'), { target: { value: 'Outra pergunta' } });
    expect(screen.queryByText('M1 · Representativo')).not.toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
