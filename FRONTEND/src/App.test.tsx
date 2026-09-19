import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App';
import { getFlowConfig } from '@/features/t4/services/t4Api';

vi.mock('@/features/health', () => ({
  useApiHealth: () => ({ status: 'online', checkAgain: vi.fn() }),
  ApiStatus: () => <span>API de teste</span>,
}));
vi.mock('@/features/t4/services/t4Api', () => ({ getFlowConfig: vi.fn(), runFlow: vi.fn() }));

function navigate(hash: string) {
  act(() => {
    window.history.replaceState(null, '', hash);
    window.dispatchEvent(new HashChangeEvent('hashchange'));
  });
}

describe('Portal acadêmico', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState(null, '', '/');
    vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
    vi.mocked(getFlowConfig).mockResolvedValue({ model: 'mistralai/mistral-large', temperature: 0.1, max_tokens: 500, prompts: { 'TRH-01': 'v0.3' }, knowledge_base: 'Base de teste.', prompt_provenance: 'Conferir originais.' });
  });
  it('abre a visão geral sem depender da API do protótipo', async () => {
    render(<App />);
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent('Um copiloto.');
    expect(screen.getAllByRole('link', { name: /^Abrir Trabalho/ })).toHaveLength(5);
    expect(screen.queryByText('API de teste')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Mistral Large' })).toHaveAttribute('href', 'https://openrouter.ai/mistralai/mistral-large');
    expect(getFlowConfig).not.toHaveBeenCalled();
  });
  it('abre uma entrega pelo endereço e navega entre páginas pelo histórico', async () => {
    window.history.replaceState(null, '', '#/entregas/2');
    render(<App />);
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent('Especificação do copiloto');
    expect(screen.getByText('71,43%')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Baixar relatório original/ })).toHaveAttribute('href', '/entregas/trabalho-02.pdf');
    navigate('#/entregas/3');
    await waitFor(() => expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Biblioteca de prompts'));
    const pending = screen.getByRole('table', { name: 'Plano de robustez ainda pendente no T3' });
    expect(within(pending).getAllByText('Pendente')).toHaveLength(4);
    expect(document.title).toBe('Aurora Tech · Trabalho 3');
    navigate('#/entregas/2');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Especificação do copiloto');
    expect(getFlowConfig).not.toHaveBeenCalled();
  });
  it('abre Sobre pelo endereço com o contexto acadêmico e os três integrantes', async () => {
    window.history.replaceState(null, '', '#/sobre');
    render(<App />);
    expect(await screen.findByRole('heading', { level: 1 })).toHaveTextContent('Conhecimento aplicado.');
    expect(screen.getByRole('heading', { name: 'Dayvson Pellegrino Rodrigues' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Denilson Bremer Procopio Ribeiro' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Leonardo Mello Ragagnin' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'IA Generativa e Aplicações com LLMs' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sobre' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByText(/não um canal oficial de atendimento de RH/)).toBeInTheDocument();
    expect(document.title).toBe('Aurora Tech · Sobre');
    expect(getFlowConfig).not.toHaveBeenCalled();
  });
  it('preserva a sessão do T4 ao visitar outra entrega', async () => {
    const user = userEvent.setup();
    window.history.replaceState(null, '', '#/entregas/4');
    render(<App />);
    const question = await screen.findByLabelText('Pergunta ao copiloto', {}, { timeout: 10000 });
    fireEvent.change(question, { target: { value: 'Minha pergunta de teste' } });
    await user.click(screen.getByRole('button', { name: /Testes e evidências/ }));
    navigate('#/entregas/1');
    await waitFor(() => expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Estudo comparativo'));
    navigate('#/entregas/4');
    expect(screen.getByRole('button', { name: /Testes e evidências/ })).toHaveAttribute('aria-current', 'page');
    await user.click(screen.getByRole('button', { name: /Protótipo/ }));
    expect(screen.getByLabelText('Pergunta ao copiloto')).toHaveValue('Minha pergunta de teste');
    expect(getFlowConfig).toHaveBeenCalledTimes(1);
  }, 15000);
});
