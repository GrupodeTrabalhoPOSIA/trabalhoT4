import type { Case, Review, Run } from '@/features/t5/types';
export interface FinalRun extends Run { release_id?: string | null; purpose?: 'evaluation' | 'smoke'; scene_id?: string | null; configuration?: Record<string, unknown>; cost_usd?: number | null; cost_source?: string }
export interface Scene { id: string; title: string; case_id: string; expected: string; statuses: string[] }
export interface Risk { id: string; title: string; level: string; cases: string[]; control: string; residual: string }
export interface Manifest { release_id: string; created_at: string; source_commit: string; configuration: Record<string, unknown>; files: Record<string, string>; fixtures: Record<string, string>; cases_sha256: string }
export interface ReleaseState { manifest: Manifest | null; frozen: boolean; drift: string[]; cases: Case[]; scenes: Scene[]; risks: Risk[]; review_case_ids: string[] }
export interface RiskReview { id: string; owner: string; controlled: boolean | null; evidence_ids: string[]; notes: string }
export interface Decision { choice: 'pendente' | 'aprovado' | 'aprovado com ressalvas' | 'reprovado'; responsible: string; rationale: string; condition: string; owner: string; deadline: string }
export interface DeliveryData {
  schema_version: number; release_id: string | null; runs: FinalRun[]; reviews: Review[]; risks: RiskReview[]; decision: Decision;
  regression_analysis: string; retrospective: string; contributions: string; demo_team: string; demo_minutes: number | null; rehearsal_notes: string; contingency: string;
}
export interface Metrics { count: number; reviewed: number; success: number | null; format: number | null; source: number | null; p95: number | null; cost: number | null; human_factuality?: number | null }
export interface Audit {
  ready: boolean; recorded: boolean; recommendation: string; decision?: string; critical?: boolean; uncontrolled?: boolean; thresholds_met?: boolean;
  issues: string[]; metrics: Metrics; candidate_metrics?: Metrics; groups: Record<string, Metrics>; reviewed_pairs: number; rubric: (number | null)[];
  rows: { case_id: string; execution_id: string | null; success: boolean | null; critical: boolean | null }[];
  smoke: (Scene & { execution_id: string | null; passed: boolean })[];
  risk_checks: (Risk & { complete: boolean; uncontrolled: boolean })[];
  excluded: { execution_id: string; case_id: string; reason: string }[];
  regressions: { case_id: string; execution_id: string; status: string; impact: string }[];
  provenance_note?: string;
}
