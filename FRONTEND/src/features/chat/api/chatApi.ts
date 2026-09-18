import { apiRequest } from '@/services/apiClient';
import type { ChatRequest, ChatResponse } from '@/types';

/** Envia uma pergunta e o histórico temporário para o backend RAG. */
export function sendChat(request: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  return apiRequest<ChatResponse>('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  });
}
