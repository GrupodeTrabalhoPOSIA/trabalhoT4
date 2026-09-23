import { describe, expect, it } from 'vitest';
import { cases } from './data';
import { casesCsv, metrics, pairedReviews, resultsCsv } from './evaluation';
import type { Review, Run } from './types';

const makeRun = (changes: Partial<Run> = {}): Run => ({
  execution_id: 'execution-1', executed_at: '2026-09-19T12:00:00Z', candidate: 't5-v1', question: 'Quantos dias?', mode: 'real', model: 'mistralai/mistral-large',
  answer: 'Resposta: Dois dias.', route: 'TRH-01', prompt_id: 'TRH-01', prompt_version: 'v0.3', valid: true, retries: 0, latency_ms: 1000, status: 'respondido', trace: [], attempts: [{ phase: 'validation', output: 'Resposta: Dois dias.', error: '' }], context: '', sources: [], document: null, error_code: null, case_id: 'P1', input_file: null, expected: 'Dois dias.', success: null, critical: null, ...changes,
});
describe('Protocolo T5', () => {
  it('usa o modelo recebido da API e não assume modelo quando ausente', () => {
    const runs = [makeRun({ model: 'vendor/custom' })];
    expect(metrics(runs, 'vendor/custom').count).toBe(1);
    expect(metrics(runs).count).toBe(0);
    expect(metrics(runs, 'vendor/other').count).toBe(0);
  });
  it('versiona 20 casos com a distribuição exigida e sete anexos', () => {
    expect(cases).toHaveLength(20);
    expect(new Set(cases.map(c => c.id)).size).toBe(20);
    expect(['representativo', 'limite', 'adversarial'].map(category => cases.filter(c => c.category === category).length)).toEqual([10, 5, 5]);
    expect(cases.filter(c => c.fixture)).toHaveLength(7);
    expect(casesCsv()).toContain('"t5-v1"');
  });
  it('preserva falhas da primeira tentativa e exclui livres e simulações da latência', () => {
    const first = makeRun({ success: false, latency_ms: 45000 });
    const retry = makeRun({ execution_id: 'retry', success: true, latency_ms: 10 });
    const free = makeRun({ case_id: 'LIVRE', success: true });
    const simulation = makeRun({ case_id: 'E1', mode: 'invalid_router', model: 'simulação determinística', success: true });
    expect(metrics([first, retry, free, simulation], 'mistralai/mistral-large')).toMatchObject({ count: 2, reviewed: 2, success: 50, p95: 45 });
    expect(resultsCsv([first, retry])).toContain('"retry"');
  });
  it('não inventa métricas e não aceita outra candidata/modelo', () => {
    expect(metrics([])).toMatchObject({ count: 0, success: null, format: null, source: null, p95: null });
    expect(metrics([makeRun({ model: 'outro' }), makeRun({ candidate: 't5-v0' })], 'mistralai/mistral-large').count).toBe(0);
  });
  it('exige pessoas distintas para a mesma execução do conjunto humano', () => {
    const review: Review = { execution_id: 'execution-1', evaluator: 'Pessoa A', scores: [5, 5, 5, 5, 5, 5, 0], notes: 'Ok', recorded_at: '2026-09-19' };
    expect(pairedReviews([makeRun()], [review, { ...review, evaluator: ' pessoa a ' }], 'mistralai/mistral-large')).toBe(0);
    expect(pairedReviews([makeRun()], [review, { ...review, evaluator: 'Pessoa B' }], 'mistralai/mistral-large')).toBe(1);
    expect(pairedReviews([makeRun()], [review, { ...review, execution_id: 'outra', evaluator: 'Pessoa B' }], 'mistralai/mistral-large')).toBe(0);
  });
  it('escapa fórmulas e preserva aspas e quebras nos resultados CSV', () => {
    expect(resultsCsv([makeRun({ answer: '=HYPERLINK("x")\nlinha' })])).toContain("'=HYPERLINK");
  });
});
