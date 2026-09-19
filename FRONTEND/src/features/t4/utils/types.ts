export type RunMode = 'real' | 'invalid_router' | 'invalid_specialist';
export interface FlowConfig {
  model: string;
  temperature: number;
  max_tokens: number;
  prompts: Record<string, string>;
  knowledge_base: string;
  prompt_provenance: string;
}
export interface FlowRequest {
  question: string;
  correction: string;
  mode: RunMode;
}
export interface ProviderDiagnostic {
  http_status: number;
  source: 'openrouter' | 'provider' | 'unknown';
  reason: 'rate_limit' | 'capacity' | 'quota' | 'credits' | 'key_credit_limit' | 'in_flight_budget' | 'request_budget' | 'unknown';
  message: string;
  retry_after_seconds?: number;
}
export interface FlowAttempt {
  phase: string;
  output: string;
  error: string;
  diagnostic?: ProviderDiagnostic;
  retry_wait_seconds?: number;
}
export interface FlowResult {
  execution_id: string;
  executed_at: string;
  question: string;
  effective_question: string;
  correction_applied: boolean;
  answer: string;
  route: string;
  prompt_id: string;
  prompt_version: string;
  valid: boolean;
  retries: number;
  latency_ms: number;
  status: string;
  model: string;
  temperature: number | null;
  max_tokens: number | null;
  mode: RunMode;
  context: string;
  trace: { id: string; state: 'completed' | 'warning' | 'failed'; detail: string }[];
  attempts: FlowAttempt[];
}
export type ReviewField = 'conclusion' | 'format' | 'factuality' | 'refusal';
export interface Evidence extends FlowResult {
  case_id: string;
  category: string;
  expected: string;
  review: Record<ReviewField, boolean | null>;
}
export interface TestCase {
  id: string;
  category: string;
  question: string;
  expected: string;
  mode: RunMode;
}
