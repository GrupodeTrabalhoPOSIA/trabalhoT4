import { afterEach, describe, expect, it, vi } from 'vitest';

import { sendChat } from './chatApi';

describe('sendChat', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('usa a base /api/v1 sem duplicar o prefixo no caminho do chat', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi.fn().mockResolvedValue({
        answer: 'Resposta da Aurora Tech.',
        sources: [],
        has_context: true,
      }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await sendChat({ message: 'Olá', history: [] });

    const requestedUrl = String(fetchMock.mock.calls[0]?.[0]);
    expect(requestedUrl).toMatch(/\/api\/v1\/chat$/);
    expect(requestedUrl).not.toContain('/api/v1/api/v1');
  });
});
