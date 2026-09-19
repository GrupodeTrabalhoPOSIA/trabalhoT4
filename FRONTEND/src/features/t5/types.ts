import type { FlowResult, RunMode } from '@/features/t4/utils/types';

export type Category = 'representativo' | 'limite' | 'adversarial';
export interface Case { id: string; category: Category; question: string; expected: string; risk: string; mode: RunMode; fixture?: string }
export interface Source { document_name: string; document_hash: string; chunk_index: number; page: number | null; content: string; relevance: number }
export interface Result extends Omit<FlowResult, 'effective_question' | 'correction_applied' | 'temperature' | 'max_tokens'> {
  candidate: string; sources: Source[]; document: { name: string; sha256: string; size_bytes: number; chunks: number; quality: string } | null; error_code: string | null;
}
export interface Run extends Result { case_id: string; input_file: string | null; expected: string; success: boolean | null; critical: boolean | null }
export interface Config { candidate: string; model: string; max_bytes: number; max_pages: number; max_characters: number; formats: string[]; top_k: number; min_relevance: number; embedding_model: string; max_context_characters: number }
export const dimensions = ['Relevância', 'Factualidade', 'Completude', 'Clareza', 'Adequação', 'Segurança', 'Qualidade multimodal'] as const;
export interface Review { execution_id: string; evaluator: string; scores: number[]; notes: string; recorded_at: string }
