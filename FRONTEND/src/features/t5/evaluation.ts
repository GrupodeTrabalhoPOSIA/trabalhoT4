import { csvCell } from '@/common/download';
import { candidate, cases, reviewCaseIds } from './data';
import { dimensions, type Review, type Run } from './types';

/** Primeira execução por caso; repetições e falhas continuam no histórico exportado. */
export function firstRuns(runs: Run[], model?: string) {
  return cases.map(c => runs.find(r => r.case_id === c.id && r.candidate === candidate && r.mode === c.mode && (r.mode !== 'real' || Boolean(model) && r.model === model))).filter((r): r is Run => Boolean(r));
}
export function metrics(runs: Run[], model?: string) {
  const first = firstRuns(runs, model);
  const real = first.filter(r => r.mode === 'real');
  const times = real.map(r => r.latency_ms).sort((a, b) => a - b);
  const generated = real.filter(r => r.attempts.some(a => a.phase === 'validation' && a.output));
  const reviewed = first.filter(r => r.success !== null);
  const sources = first.filter(r => ['M1', 'M2'].includes(r.case_id));
  return {
    count: first.length, reviewed: reviewed.length,
    success: reviewed.length ? reviewed.filter(r => r.success).length / reviewed.length * 100 : null,
    format: generated.length ? generated.filter(r => r.valid).length / generated.length * 100 : null,
    source: sources.length ? sources.filter(r => r.sources.length > 0 && r.sources.every(s => s.document_hash && s.content)).length / sources.length * 100 : null,
    p95: times.length ? times[Math.ceil(times.length * .95) - 1] / 1000 : null,
  };
}
export function pairedReviews(runs: Run[], reviews: Review[], model?: string) {
  return firstRuns(runs, model).filter(r => reviewCaseIds.includes(r.case_id) && new Set(reviews.filter(v => v.execution_id === r.execution_id).map(v => v.evaluator.trim().toLocaleLowerCase())).size >= 2).length;
}
export function csv(rows: unknown[][]) { return '\uFEFF' + rows.map(row => row.map(csvCell).join(',')).join('\r\n'); }
export function casesCsv() {
  return csv([['id', 'versao', 'categoria', 'entrada', 'arquivo', 'resultado_esperado', 'criterios', 'risco', 'modo'], ...cases.map(c => [c.id, candidate, c.category, c.question, c.fixture ?? '', c.expected, c.expected, c.risk, c.mode])]);
}
export function resultsCsv(runs: Run[]) {
  return csv([['id', 'versao', 'execucao', 'data', 'modo', 'modelo', 'arquivo', 'sha256', 'pergunta', 'esperado', 'saida', 'status', 'erro', 'formato', 'latencia_ms', 'sucesso_humano', 'eliminatorio', 'fontes'], ...runs.map(r => [r.case_id, r.candidate, r.execution_id, r.executed_at, r.mode, r.model, r.input_file, r.document?.sha256, r.question, r.expected, r.answer, r.status, r.error_code, r.valid, r.latency_ms, r.success ?? 'PENDENTE', r.critical ?? 'PENDENTE', JSON.stringify(r.sources)])]);
}
export function reviewsCsv(reviews: Review[]) {
  return csv([['execucao', 'avaliador', ...dimensions, 'observacoes', 'data'], ...reviews.map(r => [r.execution_id, r.evaluator, ...r.scores.map(v => v || 'N/A'), r.notes, r.recorded_at])]);
}
