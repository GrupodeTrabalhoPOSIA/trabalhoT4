import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { KnowledgeDocument } from '@/features/documents';
import {
  deleteDocument,
  getDocumentContent,
  listDocuments,
  uploadDocument,
} from '@/features/documents/api/documentApi';
import { ApiError } from '@/services/apiClient';
import KnowledgeBasePage from './KnowledgeBasePage';

vi.mock('@/features/documents/api/documentApi', () => ({
  listDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  deleteDocument: vi.fn(),
  getDocumentContent: vi.fn(),
}));

const document: KnowledgeDocument = {
  id: 'document-1',
  name: 'apresentacao-aurora.pdf',
  type: 'pdf',
  chunkCount: 8,
  size: 184_320,
  createdAt: '2026-08-27T12:00:00Z',
};

function getFileInput(container: HTMLElement): HTMLInputElement {
  const input = container.querySelector<HTMLInputElement>('input[type="file"]');
  if (!input) {
    throw new Error('Input de arquivo não encontrado.');
  }
  return input;
}

describe('KnowledgeBasePage integrada', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listDocuments).mockResolvedValue([document]);
    vi.mocked(uploadDocument).mockResolvedValue({
      ...document,
      id: 'document-2',
      name: 'empresa.txt',
      type: 'txt',
      chunkCount: 1,
      size: 11,
    });
    vi.mocked(deleteDocument).mockResolvedValue(undefined);
    vi.mocked(getDocumentContent).mockResolvedValue({
      id: 'document-2',
      chunks: [{ content: 'Aurora Tech', chunk_index: 0, page: null }],
    });
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  it('carrega a lista real pelo serviço', async () => {
    render(<KnowledgeBasePage />);

    expect(screen.getByText('Carregando documentos…')).toBeInTheDocument();
    expect(await screen.findByText('apresentacao-aurora.pdf')).toBeInTheDocument();
    expect(listDocuments).toHaveBeenCalledOnce();
    expect(getDocumentContent).not.toHaveBeenCalled();
  });

  it('envia um arquivo aceito e atualiza a lista', async () => {
    const { container } = render(<KnowledgeBasePage />);
    const file = new File(['Aurora Tech'], 'empresa.txt', { type: 'text/plain' });
    await screen.findByText('apresentacao-aurora.pdf');

    fireEvent.change(getFileInput(container), { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar à base' }));

    expect(await screen.findByText('empresa.txt')).toBeInTheDocument();
    expect(await screen.findByText('Aurora Tech')).toBeVisible();
    expect(uploadDocument).toHaveBeenCalledWith(file);
    expect(screen.getByText('empresa.txt foi indexado com sucesso.')).toBeInTheDocument();
  });

  it('mostra os trechos dos TXT salvos sem precisar abrir ou reenviar o arquivo', async () => {
    vi.mocked(listDocuments).mockResolvedValue([{ ...document, type: 'txt', name: 'salvo.txt' }]);
    vi.mocked(getDocumentContent).mockResolvedValue({
      id: document.id,
      chunks: [
        { content: 'Primeiro parágrafo.\n\nSegunda linha.', chunk_index: 0, page: null },
        { content: '<script>alert("texto")</script>', chunk_index: 1, page: null },
      ],
    });
    const { container, unmount } = render(<KnowledgeBasePage />);

    expect(await screen.findByText('Primeiro parágrafo. Segunda linha.')).toBeVisible();
    expect(screen.getByText('Trecho 2')).toBeVisible();
    expect(screen.getByText('<script>alert("texto")</script>')).toBeVisible();
    expect(container.querySelector('script')).toBeNull();
    expect(getDocumentContent).toHaveBeenCalledWith(document.id, expect.any(AbortSignal));

    unmount();
    render(<KnowledgeBasePage />);
    expect(await screen.findByText('Primeiro parágrafo. Segunda linha.')).toBeVisible();
    expect(getDocumentContent).toHaveBeenCalledTimes(2);
  });

  it('permite repetir a leitura do texto sem perder a lista', async () => {
    vi.mocked(listDocuments).mockResolvedValue([{ ...document, type: 'txt', name: 'salvo.txt' }]);
    vi.mocked(getDocumentContent).mockRejectedValueOnce(new Error('indisponível'));
    const user = userEvent.setup();
    render(<KnowledgeBasePage />);

    expect(await screen.findByText('Não foi possível carregar o texto deste documento.')).toBeVisible();
    expect(screen.getByText('salvo.txt')).toBeVisible();
    await user.click(screen.getByRole('button', { name: 'Tentar carregar o texto novamente' }));
    expect(await screen.findByText('Aurora Tech')).toBeVisible();
  });

  it('rejeita um formato não suportado antes de chamar a API', async () => {
    const { container } = render(<KnowledgeBasePage />);
    const file = new File(['a,b'], 'dados.csv', { type: 'text/csv' });
    await screen.findByText('apresentacao-aurora.pdf');

    fireEvent.change(getFileInput(container), { target: { files: [file] } });

    expect(screen.getByText('Formato inválido. Use PDF, TXT, MD ou DOCX.')).toBeInTheDocument();
    expect(uploadDocument).not.toHaveBeenCalled();
  });

  it('remove um documento pela API e apresenta o estado vazio', async () => {
    const user = userEvent.setup();
    render(<KnowledgeBasePage />);
    await screen.findByText('apresentacao-aurora.pdf');

    await user.click(screen.getByRole('button', { name: 'Remover apresentacao-aurora.pdf' }));

    await waitFor(() => expect(deleteDocument).toHaveBeenCalledWith('document-1'));
    expect(await screen.findByText('Nenhum documento adicionado')).toBeInTheDocument();
  });

  it('permite tentar novamente quando a listagem falha', async () => {
    vi.mocked(listDocuments)
      .mockRejectedValueOnce(new ApiError('API indisponível.', 503))
      .mockResolvedValueOnce([document]);
    const user = userEvent.setup();
    render(<KnowledgeBasePage />);

    expect(await screen.findByText('A lista não pôde ser carregada.')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Tentar novamente' }));

    expect(await screen.findByText('apresentacao-aurora.pdf')).toBeInTheDocument();
    expect(listDocuments).toHaveBeenCalledTimes(2);
  });

  it('exibe o erro de duplicidade devolvido pelo backend', async () => {
    vi.mocked(uploadDocument).mockRejectedValueOnce(
      new ApiError('Este documento já existe na base de conhecimento.', 409, 'DUPLICATE_DOCUMENT'),
    );
    const { container } = render(<KnowledgeBasePage />);
    const file = new File(['Aurora Tech'], 'duplicado.txt', { type: 'text/plain' });
    await screen.findByText('apresentacao-aurora.pdf');

    fireEvent.change(getFileInput(container), { target: { files: [file] } });
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar à base' }));

    expect(
      await screen.findByText('Este documento já existe na base de conhecimento.'),
    ).toBeInTheDocument();
  });

  it('preserva o documento quando a remoção não é confirmada', async () => {
    vi.spyOn(window, 'confirm').mockReturnValueOnce(false);
    const user = userEvent.setup();
    render(<KnowledgeBasePage />);
    await screen.findByText('apresentacao-aurora.pdf');

    await user.click(screen.getByRole('button', { name: 'Remover apresentacao-aurora.pdf' }));

    expect(deleteDocument).not.toHaveBeenCalled();
    expect(screen.getByText('apresentacao-aurora.pdf')).toBeInTheDocument();
  });
});
