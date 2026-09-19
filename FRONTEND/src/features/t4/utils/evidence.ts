import { csvCell } from '@/common/download';
import { baselineCases } from './cases';
import type { Evidence, ReviewField } from './types';

export function evidenceCsv(runs: Evidence[]): string {
  const headers = ['id', 'categoria', 'execucao_id', 'data', 'modo', 'modelo', 'temperatura', 'limite_tokens', 'pergunta', 'pergunta_efetiva', 'rota', 'prompt_versao', 'saida', 'validacao_formato_automatica', 'latencia_ms', 'repeticao', 'falha', 'status', 'conclusao_humana', 'formato_humano', 'factualidade_humana', 'recusa_humana'];
  const rows = runs.map((r) => [r.case_id, r.category, r.execution_id, r.executed_at, r.mode, r.model, r.temperature, r.max_tokens, r.question, r.effective_question, r.route, `${r.prompt_id} ${r.prompt_version}`, r.answer, r.valid, r.latency_ms, r.retries, r.attempts.filter(a => a.error).map(a => a.error).join('; '), r.status, ...Object.values(r.review).map(v => v === null ? 'PENDENTE' : v ? 'S' : 'N')]);
  return '\uFEFF' + [headers, ...rows].map(row => row.map(csvCell).join(',')).join('\r\n');
}

/** Baseline usa a PRIMEIRA execução real de cada ID; novas tentativas não apagam falhas. */
export function baselineMetrics(runs: Evidence[]): { label: string; before: string; after: string }[] {
  const firstRuns = baselineCases.map(c => runs.find(r => r.case_id === c.id && r.mode === 'real'));
  const rate = (field: ReviewField, indexes = [0, 1, 2, 3, 4, 5, 6]): string => {
    const selected = indexes.map(i => firstRuns[i]?.review[field]);
    if (selected.some(value => value === undefined || value === null)) return 'Pendente';
    return `${(selected.filter(Boolean).length / indexes.length * 100).toFixed(2).replace('.', ',')}%`;
  };
  return [
    { label: 'Conclusão', before: '100% · 7/7', after: rate('conclusion') },
    { label: 'Aderência ao formato', before: '100% · 7/7', after: rate('format') },
    { label: 'Factualidade', before: '71,43% · 5/7', after: rate('factuality') },
    { label: 'Recusa / encaminhamento', before: '100% · 2/2', after: rate('refusal', [5, 6]) },
    { label: 'Latência média', before: '3,71 s', after: firstRuns.every(Boolean) ? `${(firstRuns.reduce((sum, r) => sum + (r?.latency_ms ?? 0), 0) / 7000).toFixed(2).replace('.', ',')} s` : 'Pendente' },
  ];
}
