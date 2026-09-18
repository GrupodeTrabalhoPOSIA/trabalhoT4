import type { ChatSource } from '@/types';

/** Mensagem renderizada na conversa local. */
export interface ChatMessageView {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  hasContext?: boolean;
}
