import { downloadText } from '@/common/download';
import { baselineCases, categoryLabels, statusLabels, testCases } from '../utils/cases';
import { baselineMetrics, evidenceCsv } from '../utils/evidence';
import type { Evidence, TestCase } from '../utils/types';

export default function EvidencePanel({ runs, busy, onLoad, onInspect }: { runs: Evidence[]; busy: boolean; onLoad: (testCase: TestCase) => void; onInspect: (id: string) => void }) {
  const completed = testCases.filter(c => runs.some(r => r.case_id === c.id)).length;
  return <section className="t4-evidence" aria-labelledby="evidence-heading">
    <div className="t4-section-heading"><div><span className="eyebrow">Caderno de execução</span><h2 id="evidence-heading">Testes e evidências</h2><p>{completed} de 13 casos com execução registrada nesta sessão. Executado não significa aprovado.</p></div><div className="t4-export-actions"><button className="t4-secondary-button" disabled={!runs.length} onClick={() => downloadText('resultados_t4.csv', evidenceCsv(runs), 'text/csv;charset=utf-8')}>Exportar CSV</button><button className="primary-button" disabled={!runs.length} onClick={() => downloadText('evidencias_t4.json', JSON.stringify({ project: 'Aurora Tech · Trabalho 4', exported_at: new Date().toISOString(), runs }, null, 2), 'application/json')}>Exportar evidências JSON</button></div></div>
    <p className="t4-notice">Registros mantidos apenas nesta página. Exporte antes de recarregar ou fechar. O CSV guarda resultados e avaliação; o JSON inclui contexto, etapas e saídas brutas. Nenhum arquivo do repositório é atualizado automaticamente.</p>
    <div className="t4-table-wrap"><table className="t4-table"><caption>13 casos obrigatórios · catálogo versionado em tests/casos.csv</caption><thead><tr><th>Caso</th><th>Pergunta / comportamento esperado</th><th>Registro nesta sessão</th><th>Ação</th></tr></thead><tbody>{testCases.map(c => {
      const related = runs.filter(r => r.case_id === c.id);
      return <tr key={c.id}><td><strong>{c.id}</strong><small>{categoryLabels[c.category]}</small></td><td>{c.question}<small>{c.expected}</small></td><td><span className={`t4-pill ${!related.length ? 't4-pill--neutral' : ''}`}>{related.length ? `${related.length} execução(ões)` : 'Pendente'}</span>{c.mode !== 'real' && <small>Simulação identificada</small>}</td><td><button className="t4-text-button" disabled={busy} onClick={() => onLoad(c)}>Carregar {c.id} →</button></td></tr>;
    })}</tbody></table></div>
    <div className="t4-section-heading t4-section-heading--spaced"><div><span className="eyebrow">Continuidade com o Trabalho 2</span><h2>Comparação com o baseline</h2><p>Reaplique os sete casos originais e revise as primeiras respostas. Repetições ficam preservadas.</p></div></div>
    <div className="t4-baseline-cases">{baselineCases.map(c => <button disabled={busy} key={c.id} className="t4-secondary-button" title={c.question} onClick={() => onLoad(c)}>{c.id} · {runs.some(r => r.case_id === c.id && r.mode === 'real') ? 'Registrado' : 'Executar'}</button>)}</div>
    <div className="t4-table-wrap"><table className="t4-table"><caption>Mesmas métricas do T2 · apenas execuções reais de R1–R5 e L1–L2</caption><thead><tr><th>Métrica</th><th>Baseline T2</th><th>Fluxo T4 · sessão atual</th></tr></thead><tbody>{baselineMetrics(runs).map(m => <tr key={m.label}><td>{m.label}</td><td>{m.before}</td><td>{m.after}</td></tr>)}</tbody></table></div>
    <p className="t4-muted">Referência T2: Mistral Large. Confira o modelo registrado em cada execução; uma troca de modelo limita a comparação. Tokens e custos não são disponibilizados pelo cliente atual e não são estimados.</p>
    <h2 className="t4-history-title">Histórico de execuções <small>({runs.length})</small></h2>
    {runs.length ? <ol className="t4-run-history">{runs.map((r, i) => <li key={r.execution_id}><button onClick={() => onInspect(r.execution_id)}><strong>#{i + 1} · {r.case_id}</strong><span>{statusLabels[r.status] ?? r.status}</span><small>{r.mode === 'real' ? r.model : 'Simulação'} · {r.prompt_id} {r.prompt_version} · {(r.latency_ms / 1000).toFixed(2)} s</small></button></li>)}</ol> : <p className="t4-muted">Nenhuma execução nesta sessão. Carregue um caso e execute o fluxo no protótipo.</p>}
  </section>;
}
