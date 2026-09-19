import type { DeliveryData, FinalRun } from './types';
import type { Review, Run } from '@/features/t5/types';

export function emptyDelivery(releaseId: string): DeliveryData {
  return { schema_version: 1, release_id: releaseId, runs: [], reviews: [], risks: [], decision: { choice: 'pendente', responsible: '', rationale: '', condition: '', owner: '', deadline: '' }, regression_analysis: '', retrospective: '', contributions: '', demo_team: '', demo_minutes: null, rehearsal_notes: '', contingency: '' };
}
function record(value: unknown): value is Record<string, unknown> { return typeof value === 'object' && value !== null && !Array.isArray(value); }
export function parseEvidence(text: string, releaseId: string): DeliveryData {
  if (text.length > 10_000_000) throw new Error('O arquivo de evidências deve ter até 10 MB.');
  const value: unknown = JSON.parse(text);
  if (!record(value) || !Array.isArray(value.runs) || value.runs.length > 200 || !Array.isArray(value.reviews) || value.reviews.length > 100) throw new Error('Use o JSON de evidências do T5 ou T6, com listas de execuções e avaliações.');
  for (const run of value.runs) {
    if (!record(run) || !['execution_id', 'case_id', 'answer', 'question', 'mode', 'model', 'status', 'executed_at', 'candidate'].every(key => typeof run[key] === 'string') || !Array.isArray(run.sources) || !Array.isArray(run.attempts) || typeof run.valid !== 'boolean' || typeof run.latency_ms !== 'number' || !Number.isFinite(run.latency_ms) || ![null, true, false].includes(run.success as null | boolean) || ![null, true, false].includes(run.critical as null | boolean)) throw new Error('Registro de execução inválido. Os dados atuais foram preservados.');
    if (!(run.sources as unknown[]).every(s => record(s) && ['document_name', 'document_hash', 'content'].every(k => typeof s[k] === 'string') && Number.isInteger(s.chunk_index) && (s.page === null || Number.isInteger(s.page)))) throw new Error('Fonte de evidência inválida.');
    if (run.cost_usd != null && (typeof run.cost_usd !== 'number' || !Number.isFinite(run.cost_usd) || run.cost_usd < 0 || run.cost_usd > 1000)) throw new Error('Custo observado inválido.');
    if (run.cost_source != null && typeof run.cost_source !== 'string') throw new Error('Referência de custo inválida.');
  }
  for (const review of value.reviews) {
    if (!record(review) || !['execution_id', 'evaluator', 'notes', 'recorded_at'].every(key => typeof review[key] === 'string') || !Array.isArray(review.scores) || review.scores.length !== 7 || !review.scores.every(score => Number.isInteger(score) && score >= 0 && score <= 5)) throw new Error('Registro de rubrica inválido.');
  }
  const result = emptyDelivery(releaseId);
  result.runs = value.runs as FinalRun[]; result.reviews = value.reviews as Review[];
  // Só imports T6 trazem formulários. O servidor revalida todos os campos antes do gate.
  if (value.schema_version === 1) {
    const fields = ['regression_analysis', 'retrospective', 'contributions', 'demo_team', 'rehearsal_notes', 'contingency'] as const;
    for (const key of fields) if (typeof value[key] === 'string' && value[key].length <= 5000) result[key] = value[key];
    if (typeof value.demo_minutes === 'number' && Number.isInteger(value.demo_minutes) && value.demo_minutes > 0 && value.demo_minutes <= 120) result.demo_minutes = value.demo_minutes;
    if (Array.isArray(value.risks) && value.risks.length <= 5 && value.risks.every(r => record(r) && ['id', 'owner', 'notes'].every(key => typeof r[key] === 'string') && [null, true, false].includes(r.controlled as null | boolean) && Array.isArray(r.evidence_ids) && r.evidence_ids.every(id => typeof id === 'string'))) result.risks = value.risks as DeliveryData['risks'];
    if (record(value.decision) && ['choice', 'responsible', 'rationale', 'condition', 'owner', 'deadline'].every(key => typeof (value.decision as Record<string, unknown>)[key] === 'string') && ['pendente', 'aprovado', 'aprovado com ressalvas', 'reprovado'].includes(String(value.decision.choice))) result.decision = value.decision as unknown as DeliveryData['decision'];
  }
  return result;
}

/** IDs repetidos nunca sobrescrevem saídas, revisões ou falhas anteriores. */
export function mergeEvidence(current: DeliveryData, incoming: DeliveryData): DeliveryData {
  const ids = new Set(current.runs.map(run => run.execution_id));
  const reviewIds = new Set(current.reviews.map(r => `${r.execution_id}:${r.evaluator.trim().toLocaleLowerCase()}`));
  const merged = { ...current, runs: [...current.runs, ...incoming.runs.filter(r => { if (ids.has(r.execution_id)) return false; ids.add(r.execution_id); return true; })], reviews: [...current.reviews, ...incoming.reviews.filter(r => { const key = `${r.execution_id}:${r.evaluator.trim().toLocaleLowerCase()}`; if (reviewIds.has(key)) return false; reviewIds.add(key); return true; })] };
  if (merged.runs.length > 200 || merged.reviews.length > 100) throw new Error('Limite da campanha: 200 execuções e 100 avaliações. Exporte o histórico antes de iniciar outra campanha.');
  return merged;
}

let t5Session: { runs: Run[]; reviews: Review[] } = { runs: [], reviews: [] };
export function publishT5Session(runs: Run[], reviews: Review[]) { t5Session = { runs, reviews }; }
export function getT5Session() { return t5Session; }
