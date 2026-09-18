import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { sendChat } from '@/features/chat/api/chatApi';
import { ApiError } from '@/services/apiClient';
import type { ChatResponse } from '@/types';
import ChatPage from './ChatPage';

vi.mock('@/features/chat/api/chatApi', () => ({
  sendChat: vi.fn(),
}));

const contextualResponse: ChatResponse = {
  answer: 'A Aurora Tech oferece consultoria em transformação digital.',
  sources: [
    {
      document_id: 'document-1',
      document_name: 'servicos.pdf',
      page: 2,
    },
  ],
  has_context: true,
};

async function ask(question: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Sua pergunta'), question);
  await user.click(screen.getByRole('button', { name: 'Enviar' }));
  return user;
}

describe('ChatPage integrada', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('mostra a pergunta imediatamente e depois renderiza resposta e fonte', async () => {
    let resolveResponse: (response: ChatResponse) => void = () => undefined;
    vi.mocked(sendChat).mockReturnValue(
      new Promise((resolve) => {
        resolveResponse = resolve;
      }),
    );
    render(<ChatPage />);

    await ask('Quais serviços são oferecidos?');

    expect(screen.getByText('Quais serviços são oferecidos?')).toBeInTheDocument();
    expect(screen.getByText('Aurora está preparando uma resposta')).toBeInTheDocument();
    resolveResponse(contextualResponse);

    expect(await screen.findByText(contextualResponse.answer)).toBeInTheDocument();
    expect(screen.getByText('servicos.pdf · pág. 2')).toBeInTheDocument();
    expect(vi.mocked(sendChat).mock.calls[0]?.[0]).toEqual({
      message: 'Quais serviços são oferecidos?',
      history: [],
    });
  });

  it('envia apenas o histórico local anterior na pergunta seguinte', async () => {
    vi.mocked(sendChat).mockResolvedValue(contextualResponse);
    render(<ChatPage />);

    await ask('Primeira pergunta');
    await screen.findByText(contextualResponse.answer);
    await ask('Segunda pergunta');

    await waitFor(() => expect(sendChat).toHaveBeenCalledTimes(2));
    expect(vi.mocked(sendChat).mock.calls[1]?.[0]).toEqual({
      message: 'Segunda pergunta',
      history: [
        { role: 'user', content: 'Primeira pergunta' },
        { role: 'assistant', content: contextualResponse.answer },
      ],
    });
  });

  it('identifica visualmente uma resposta sem contexto', async () => {
    vi.mocked(sendChat).mockResolvedValue({
      answer: 'Não encontrei informações suficientes na base de conhecimento.',
      sources: [],
      has_context: false,
    });
    render(<ChatPage />);

    await ask('Qual é a cotação do dólar?');

    expect(await screen.findByText('Sem contexto suficiente')).toBeInTheDocument();
    expect(screen.queryByLabelText('Fontes da resposta')).not.toBeInTheDocument();
  });

  it('apresenta um erro compreensível retornado pela API', async () => {
    vi.mocked(sendChat).mockRejectedValue(
      new ApiError('O modelo demorou demais para responder. Tente novamente.', 504, 'MODEL_TIMEOUT'),
    );
    render(<ChatPage />);

    await ask('Pergunta lenta');

    expect(
      await screen.findByText('O modelo demorou demais para responder. Tente novamente.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Tentar novamente' })).toBeInTheDocument();
  });

  it('limpa todas as mensagens visíveis sem chamar o backend', async () => {
    vi.mocked(sendChat).mockResolvedValue(contextualResponse);
    render(<ChatPage />);
    const user = await ask('Pergunta temporária');
    await screen.findByText(contextualResponse.answer);

    await user.click(screen.getByRole('button', { name: 'Limpar conversa' }));

    expect(screen.queryByText('Pergunta temporária')).not.toBeInTheDocument();
    expect(screen.queryByText(contextualResponse.answer)).not.toBeInTheDocument();
    expect(screen.getByText('Nova conversa')).toBeInTheDocument();
    expect(sendChat).toHaveBeenCalledOnce();
  });

  it('permite enviar com Enter diretamente no campo de pergunta', async () => {
    vi.mocked(sendChat).mockResolvedValue(contextualResponse);
    const user = userEvent.setup();
    render(<ChatPage />);

    await user.click(screen.getByLabelText('Sua pergunta'));
    await user.keyboard('Pergunta pelo teclado');
    expect(screen.getByLabelText('Sua pergunta')).toHaveFocus();
    await user.keyboard('{Enter}');

    expect(await screen.findByText(contextualResponse.answer)).toBeInTheDocument();
  });

  it('mantém somente as dez mensagens mais recentes no payload', async () => {
    vi.mocked(sendChat).mockResolvedValue(contextualResponse);
    render(<ChatPage />);

    for (let index = 1; index <= 7; index += 1) {
      await ask(`Pergunta ${index}`);
      await waitFor(() => expect(sendChat).toHaveBeenCalledTimes(index));
      await waitFor(() => expect(screen.queryByText('Enviando…')).not.toBeInTheDocument());
    }

    const lastRequest = vi.mocked(sendChat).mock.calls[6]?.[0];
    expect(lastRequest?.history).toHaveLength(10);
    expect(lastRequest?.history[0]).toEqual({ role: 'user', content: 'Pergunta 2' });
  });

  it('repete uma solicitação com erro sem duplicar a mensagem do usuário', async () => {
    vi.mocked(sendChat)
      .mockRejectedValueOnce(new ApiError('Falha temporária.', 502))
      .mockResolvedValueOnce(contextualResponse);
    render(<ChatPage />);
    const user = await ask('Pergunta única');
    await screen.findByText('Falha temporária.');

    await user.click(screen.getByRole('button', { name: 'Tentar novamente' }));

    expect(await screen.findByText(contextualResponse.answer)).toBeInTheDocument();
    expect(screen.getAllByText('Pergunta única')).toHaveLength(1);
    expect(sendChat).toHaveBeenCalledTimes(2);
  });

  it('renderiza Markdown e bloqueia URLs e HTML perigosos', async () => {
    vi.mocked(sendChat).mockResolvedValue({
      answer: '**Resposta segura** [link](javascript:alert(1)) <script>alert(2)</script>',
      sources: [],
      has_context: true,
    });
    const { container } = render(<ChatPage />);

    await ask('Teste de segurança');

    expect(await screen.findByText('Resposta segura')).toHaveProperty('tagName', 'STRONG');
    expect(container.querySelector('script')).toBeNull();
    expect(screen.getByText('link').closest('a')).not.toHaveAttribute('href');
  });
});
