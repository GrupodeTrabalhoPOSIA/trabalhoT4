/** Estado observado da API no frontend. */
export type ApiAvailability = 'checking' | 'online' | 'offline';

/** Resposta do endpoint de saúde. */
export interface HealthResponse {
  status: 'ok';
}

/** Item do histórico temporário enviado ao backend. */
export interface ChatHistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

/** Contrato público para envio de pergunta. */
export interface ChatRequest {
  message: string;
  history: ChatHistoryMessage[];
}

/** Fonte utilizada em uma resposta. */
export interface ChatSource {
  document_id: string;
  document_name: string;
  page: number | null;
}

/** Contrato público da resposta do chat. */
export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  has_context: boolean;
}

/** Corpo padronizado de erro retornado pela API. */
export interface ApiErrorResponse {
  detail: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

