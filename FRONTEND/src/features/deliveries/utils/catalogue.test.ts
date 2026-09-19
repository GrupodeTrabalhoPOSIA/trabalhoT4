import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { sourceReports } from '../services/sourceReports';
import { deliveries, pageFromHash, pagePaths, reports } from './catalogue';

describe('Catálogo das entregas', () => {
  it('possui uma rota direta e única para cada página', () => {
    expect(new Set(Object.values(pagePaths)).size).toBe(10);
    for (const [page, hash] of Object.entries(pagePaths)) expect(pageFromHash(hash)).toBe(page);
    expect(pageFromHash('')).toBe('overview');
    expect(pageFromHash('#/inexistente')).toBe('overview');
    expect(deliveries.map(item => item.id)).toEqual(['t1', 't2', 't3', 't4', 't5', 't6']);
  });
  it.each(Object.entries(sourceReports))('publica uma cópia íntegra do relatório %s', (_, source) => {
    const content = readFileSync(resolve(process.cwd(), 'public', source.href.slice(1)));
    expect(createHash('sha256').update(content).digest('hex')).toBe(source.sha256);
  });
  it('mantém os resultados históricos e as pendências explícitas', () => {
    expect(reports.t2.metrics.find(metric => metric.label === 'Factualidade')?.value).toBe('71,43%');
    expect(reports.t2.tables[1].rows).toHaveLength(7);
    expect(reports.t3.tables[2].rows).toHaveLength(4);
    expect(reports.t3.tables[2].rows.every(row => row[3] === 'Pendente')).toBe(true);
    expect(reports.t3.limitations.join(' ')).toContain('precisam ser conferidos');
    for (const report of Object.values(reports)) {
      for (const table of report.tables) expect(table.rows.every(row => row.length === table.columns.length)).toBe(true);
    }
  });
});
