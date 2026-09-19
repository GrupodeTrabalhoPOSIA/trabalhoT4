import { describe, expect, it } from 'vitest';
import { baselineMetrics, evidenceCsv } from './evidence';
import type { Evidence } from './types';
import { baselineCases, testCases } from './cases';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import source from './cases.csv?raw';

describe('Rastreabilidade das evidências', () => {
  it('mantém a cópia de apresentação sincronizada com o catálogo entregue', () => {
    const catalog = readFileSync(resolve(process.cwd(), '../tests/casos.csv'), 'utf-8');
    expect(source.trim().replaceAll('\r\n', '\n')).toBe(catalog.trim().replaceAll('\r\n', '\n'));
  });
  it('lê os 13 casos do catálogo, com simulações somente E1 e E2', () => {
    expect(testCases).toHaveLength(13);
    expect(testCases.filter(c => c.mode !== 'real').map(c => c.id)).toEqual(['E1', 'E2']);
  });
  it('não troca a primeira falha por uma repetição bem-sucedida', () => {
    const runs = baselineCases.map(c => ({ case_id: c.id, mode: 'real', latency_ms: 1000, review: { conclusion: true, format: true, factuality: c.id !== 'R2', refusal: true } } as Evidence));
    runs.push({ ...runs[1], review: { ...runs[1].review, factuality: true } });
    expect(baselineMetrics(runs).find(m => m.label === 'Factualidade')?.after).toBe('85,71%');
    expect(baselineMetrics(runs).find(m => m.label === 'Latência média')?.after).toBe('1,00 s');
  });
  it('exporta falhas e protege células com fórmulas', () => {
    const output = evidenceCsv([{ case_id: 'E2', question: '=SUM(1,1)', answer: 'a,"b"\nc', attempts: [{ phase: 'validation', error: 'INVALID_FORMAT', output: 'erro' }], review: { conclusion: null, format: null, factuality: null, refusal: null }, mode: 'invalid_specialist' } as Evidence]);
    expect(output).toContain("'=SUM(1,1)");
    expect(output).toContain('a,""b""\nc');
    expect(output).toContain('INVALID_FORMAT');
    expect(output).toContain('PENDENTE');
  });
});
