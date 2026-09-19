import { flowSteps } from '../utils/cases';
import type { Evidence } from '../utils/types';

export default function FlowTrace({ result, busy }: { result: Evidence | null; busy: boolean }) {
  return (
    <aside className="t4-trace" aria-labelledby="trace-heading">
      <div className="t4-panel-heading"><span className="eyebrow">Orquestração</span><h2 id="trace-heading">O caminho da resposta</h2></div>
      <p className="t4-muted">{busy ? 'Execução em andamento. O registro será exibido ao concluir.' : result ? 'Registro devolvido pelo backend nesta execução.' : 'Fluxo previsto. Execute uma pergunta para inspecionar as etapas percorridas.'}</p>
      <ol className="t4-steps">
        {flowSteps.map(([id, label], index) => {
          const events = result?.trace.filter(step => step.id === id) ?? [];
          const state = events.at(-1)?.state;
          return <li key={id} className={state ? `t4-step t4-step--${state}` : 't4-step'}>
            <span className="t4-step-number" aria-hidden="true">{state === 'completed' ? '✓' : String(index + 1).padStart(2, '0')}</span>
            <div><strong>{label}</strong><small>{events.length ? events.map(e => e.detail).join(' ') : result ? 'Não executada neste caminho.' : 'Aguardando execução'}</small></div>
          </li>;
        })}
      </ol>
      <div className="t4-exceptions"><strong>Caminhos de exceção</strong><p>Dado ausente ou baixa confiança → perguntar.<br />Fora do escopo → recusar / encaminhar.<br />Falha técnica ou de formato → repetir uma vez; depois, resposta segura.</p></div>
    </aside>
  );
}
