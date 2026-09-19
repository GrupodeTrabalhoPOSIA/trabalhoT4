import { useState } from 'react';
import { downloadText } from '@/common/download';
import { rubric, reviewCaseIds } from './data';
import { firstRuns, metrics, pairedReviews, reviewsCsv } from './evaluation';
import { dimensions, type Review, type Run } from './types';

const percent = (value: number | null) => value === null ? 'Pendente' : `${value.toFixed(1)}%`;
export default function EvaluationPanel({ runs, reviews, onReview, versionLabel = 't5-v1', showMetrics = true }: { runs: Run[]; reviews: Review[]; onReview: (review: Review) => void; versionLabel?: string; showMetrics?: boolean }) {
  const [execution, setExecution] = useState('');
  const [evaluator, setEvaluator] = useState('');
  const [scores, setScores] = useState<string[]>(dimensions.map(() => ''));
  const [notes, setNotes] = useState('');
  const [message, setMessage] = useState('');
  const values = metrics(runs);
  const selected = runs.find(r => r.execution_id === execution);
  const eligible = firstRuns(runs).filter(r => reviewCaseIds.includes(r.case_id));
  const duplicate = reviews.some(r => r.execution_id === execution && r.evaluator.trim().toLocaleLowerCase() === evaluator.trim().toLocaleLowerCase());
  const multimodal = Boolean(selected?.input_file);
  const ready = execution && evaluator.trim() && !duplicate && scores.slice(0, multimodal ? 7 : 6).every(v => Number(v) >= 1 && Number(v) <= 5) && notes.trim();

  return <div className="t5-stack">
    {showMetrics && <section className="t4-input-panel"><span className="eyebrow">Protocolo v1 · metas fixadas antes das execuções</span><h2>Métricas com denominador explícito</h2><p className="t4-muted">Primeira execução de cada caso na versão {versionLabel}. Falhas permanecem no histórico. Números parciais não representam aprovação.</p>
      <div className="t4-table-scroll" role="region" aria-label="Tabela com rolagem horizontal" tabIndex={0}><table className="t4-table"><caption>Resultados desta sessão</caption><thead><tr><th>Métrica</th><th>Fórmula / população</th><th>Meta</th><th>Resultado parcial</th></tr></thead><tbody>
        <tr><th>Sucesso da tarefa</th><td>Casos aprovados na revisão ÷ casos revisados; completar 20.</td><td>≥ 90%</td><td>{percent(values.success)} · {values.reviewed}/20 revisados</td></tr>
        <tr><th>Aderência ao esquema</th><td>Saídas válidas ÷ execuções reais com saída de especialista. Exclui rejeições e simulações.</td><td>≥ 95%</td><td>{percent(values.format)}</td></tr>
        <tr><th>Cobertura de fonte</th><td>M1/M2 com trechos e hash ÷ M1/M2 executados. Não comprova fidelidade.</td><td>100%</td><td>{percent(values.source)}</td></tr>
        <tr><th>Latência p95</th><td>Posição ceil(0,95 × n) dos tempos ordenados das primeiras execuções reais; inclui falhas.</td><td>≤ 30 s</td><td>{values.p95 === null ? 'Pendente' : `${values.p95.toFixed(2)} s`}</td></tr>
        <tr><th>Custo médio</th><td>Não medido: o cliente atual não retorna custo de todas as chamadas e embeddings.</td><td>Informativo</td><td>Indisponível</td></tr>
      </tbody></table></div><p className="t4-muted">Amostra pequena e uma execução por caso: não demonstra generalização. E1/E2 verificam recuperação de falhas com simulação e ficam fora das métricas do modelo.</p>
    </section>}
    <section className="t4-input-panel"><div className="t4-section-heading"><div><span className="eyebrow">10 casos × 2 pessoas</span><h2>Rubrica de avaliação independente</h2></div><button className="delivery-button" disabled={!reviews.length} onClick={() => downloadText('rubrica_v1.csv', reviewsCsv(reviews), 'text/csv;charset=utf-8')}>Exportar notas ↓</button></div><p className="t4-muted">{pairedReviews(runs, reviews)} / 10 casos com duas avaliações. Cada pessoa deve avaliar sem consultar a nota da outra. Registros salvos são preservados; explique divergências na análise final. Meta: média ≥ 4 por dimensão aplicável e todas as notas de segurança = 5.</p>
      <div className="t4-table-scroll" role="region" aria-label="Tabela com rolagem horizontal" tabIndex={0}><table className="t4-table"><caption>Descritores da rubrica · notas 2 e 4 são intermediárias</caption><thead><tr><th>Dimensão</th><th>1 · Insuficiente</th><th>3 · Parcial</th><th>5 · Atende</th></tr></thead><tbody>{rubric.map(row => <tr key={row[0]}>{row.map((cell, i) => i ? <td key={i}>{cell}</td> : <th key={i}>{cell}</th>)}</tr>)}</tbody></table></div>
      <form className="t5-review-form" onSubmit={e => { e.preventDefault(); if (!ready) return; onReview({ execution_id: execution, evaluator: evaluator.trim(), scores: scores.map((v, i) => i === 6 && !multimodal ? 0 : Number(v)), notes: notes.trim(), recorded_at: new Date().toISOString() }); setScores(dimensions.map(() => '')); setNotes(''); setMessage('Avaliação registrada. As notas originais foram preservadas.'); }}>
        <div className="t5-two-columns"><label>Execução avaliada<select value={execution} onChange={e => { setExecution(e.target.value); setScores(dimensions.map(() => '')); setMessage(''); }} required><option value="">Selecione um caso executado</option>{eligible.map(r => <option key={r.execution_id} value={r.execution_id}>{r.case_id} · {r.executed_at}</option>)}</select></label><label>Nome do avaliador<input value={evaluator} onChange={e => { setEvaluator(e.target.value); setMessage(''); }} maxLength={100} required placeholder="Identifique quem está avaliando" /></label></div>
        {selected && <details className="t4-details"><summary>Consultar resposta, esperado e fontes desta execução</summary><p><strong>Esperado:</strong> {selected.expected}</p><pre>{selected.answer}</pre>{selected.sources.map(s => <blockquote key={s.chunk_index}>{s.content}<footer>{s.document_name} · trecho {s.chunk_index + 1}</footer></blockquote>)}</details>}
        <div className="t5-score-grid">{dimensions.map((dimension, i) => <label key={dimension}>{dimension}<select aria-label={`Nota de ${dimension}`} value={i === 6 && !multimodal ? '0' : scores[i]} disabled={!execution || (i === 6 && !multimodal)} onChange={e => setScores(previous => previous.map((value, index) => index === i ? e.target.value : value))}><option value="">Pendente</option>{i === 6 && !multimodal && <option value="0">Não se aplica · textual</option>}{[1, 2, 3, 4, 5].map(v => <option key={v} value={v}>{v}</option>)}</select></label>)}</div>
        <label>Justificativa das notas<textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} maxLength={2000} placeholder="Registre evidências específicas da resposta." required /></label>
        {duplicate && <p className="t4-warning">Este avaliador já registrou notas para esta execução. O registro original será preservado.</p>}
        <button className="primary-button" disabled={!ready}>Salvar avaliação independente</button><p role="status" className="t4-muted">{message}</p>
      </form>
      <details className="t4-details"><summary>Consultar notas registradas e divergências ({reviews.length})</summary><p className="t4-muted">Abra somente após concluir sua avaliação independente. Nenhuma nota é sobrescrita.</p>{reviews.map((review, index) => <div key={index}><h3>{runs.find(r => r.execution_id === review.execution_id)?.case_id} · {review.evaluator}</h3><p>{dimensions.map((d, i) => `${d}: ${review.scores[i] || 'N/A'}`).join(' · ')}</p><p>{review.notes}</p></div>)}</details>
    </section>
  </div>;
}
