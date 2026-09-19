import MarkdownContent from '@/features/chat/components/MarkdownContent';
import { PROJECT_MODEL_ID } from '@/common/modelPolicy';
import { statusLabels } from '../utils/cases';
import type { Evidence, ReviewField } from '../utils/types';

const reviewFields: [ReviewField, string][] = [['conclusion', 'Concluiu a tarefa?'], ['format', 'Formato adequado?'], ['factuality', 'Sem informação inventada?'], ['refusal', 'Encaminhamento / recusa correto?']];

export default function RunResult({ run, onReview, onCorrect }: { run: Evidence; onReview: (id: string, field: ReviewField, value: boolean | null) => void; onCorrect: () => void }) {
  return <section className="t4-result" aria-labelledby="result-heading">
    <div className="t4-result-heading"><span className={`t4-pill ${run.valid ? '' : 't4-pill--warning'}`}>{statusLabels[run.status] ?? run.status}</span><small>{run.mode === 'real' ? 'Execução real' : 'Simulação · sem chamada ao modelo'}</small></div>
    <h2 id="result-heading">Resposta do copiloto</h2>
    {run.mode === 'real' && run.model !== PROJECT_MODEL_ID && <p className="t4-notice" role="alert">Esta execução informa um modelo diferente de {PROJECT_MODEL_ID}. O registro foi preservado, mas não pode ser usado como comparação com o baseline Mistral Large.</p>}
    <MarkdownContent content={run.answer} />
    <dl className="t4-run-metrics">
      <div><dt>Rota / prompt</dt><dd>{run.prompt_id} <small>{run.prompt_version}</small></dd></div>
      <div><dt>Latência</dt><dd>{(run.latency_ms / 1000).toFixed(2)} s</dd></div>
      <div><dt>Repetições</dt><dd>{run.retries} / 1</dd></div>
      <div><dt>Validação automática</dt><dd>{run.valid ? 'Contrato aceito' : 'Falha / fallback'}</dd></div>
    </dl>
    <p className="t4-muted">Formato validado não significa factualidade comprovada. Compare a resposta com a política antes de aprová-la.</p>
    <button className="t4-text-button" type="button" onClick={onCorrect}>Corrigir ou complementar minha pergunta →</button>
    <details className="t4-details"><summary>Contexto e saídas brutas</summary>
      <p><strong>Modelo:</strong> {run.model}</p><p><strong>Pergunta efetiva:</strong> {run.effective_question}</p>
      {run.correction_applied && <p>A correção substituiu a pergunta anterior; nenhuma conversa antiga foi enviada.</p>}
      <h3>Base enviada ao especialista</h3><pre>{run.context || 'Especialista não foi chamado.'}</pre>
      {run.attempts.map((attempt, index) => <div key={index}><h3>Tentativa {index + 1} · {attempt.phase}</h3>{attempt.error && <p className="t4-warning">{attempt.error}</p>}<pre>{attempt.output || 'Sem resposta do provedor.'}</pre></div>)}
    </details>
    <details className="t4-details"><summary>Registrar avaliação humana</summary>
      <p className="t4-muted">Use o resultado esperado do caso e a base autorizada. A aprovação nunca é preenchida automaticamente.</p>
      <div className="t4-review-grid">{reviewFields.map(([field, label]) => <label key={field}>{label}<select value={run.review[field] === null ? '' : String(run.review[field])} onChange={e => onReview(run.execution_id, field, e.target.value === '' ? null : e.target.value === 'true')}><option value="">Pendente</option><option value="true">Sim</option><option value="false">Não</option></select></label>)}</div>
    </details>
  </section>;
}
