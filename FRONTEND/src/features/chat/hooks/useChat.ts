import { useCallback, useRef, useState } from 'react';

import { sendChat } from '@/features/chat/api/chatApi';
import type { ChatMessageView } from '@/features/chat/types/chat';
import { ApiError } from '@/services/apiClient';
import type { ChatHistoryMessage } from '@/types';

const MAX_HISTORY_MESSAGES = 10;
const REQUEST_TIMEOUT_MS = 45_000;

function createMessageId(): string {
  return crypto.randomUUID();
}

function toHistory(messages: ChatMessageView[]): ChatHistoryMessage[] {
  return messages.slice(-MAX_HISTORY_MESSAGES).map(({ role, content }) => ({ role, content }));
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof DOMException && error.name === 'AbortError') {
    return 'A resposta demorou demais. Tente novamente.';
  }
  return 'Não foi possível obter uma resposta. Verifique a API e tente novamente.';
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessageView[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastRequest = useRef<{ question: string; history: ChatHistoryMessage[] } | null>(null);

  const performRequest = useCallback(
    async (question: string, history: ChatHistoryMessage[], appendUser: boolean) => {
      if (isSending) {
        return;
      }

      lastRequest.current = { question, history };
      setError(null);
      setIsSending(true);
      if (appendUser) {
        setMessages((current) => [
          ...current,
          { id: createMessageId(), role: 'user', content: question },
        ]);
      }

      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
      try {
        const response = await sendChat({ message: question, history }, controller.signal);
        setMessages((current) => [
          ...current,
          {
            id: createMessageId(),
            role: 'assistant',
            content: response.answer,
            sources: response.sources,
            hasContext: response.has_context,
          },
        ]);
        lastRequest.current = null;
      } catch (requestError) {
        setError(errorMessage(requestError));
      } finally {
        window.clearTimeout(timeoutId);
        setIsSending(false);
      }
    },
    [isSending],
  );

  const submit = useCallback(
    async (rawQuestion: string) => {
      const question = rawQuestion.trim();
      if (!question) {
        return;
      }
      await performRequest(question, toHistory(messages), true);
    },
    [messages, performRequest],
  );

  const retry = useCallback(() => {
    const request = lastRequest.current;
    if (request) {
      void performRequest(request.question, request.history, false);
    }
  }, [performRequest]);

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
    lastRequest.current = null;
  }, []);

  return { messages, isSending, error, submit, retry, clear };
}
