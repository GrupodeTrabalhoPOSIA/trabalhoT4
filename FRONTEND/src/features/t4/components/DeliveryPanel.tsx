import type { FlowConfig } from '../utils/types';

const requirements = [
  ['Fluxo e exceções', 'Etapas exibidas no protótipo com registro da execução e saídas para esclarecimento, recusa e fallback.', 'architecture/fluxo.png'],
  ['Protótipo executável', 'Interface conectada a POST /api/v1/t4/run. Templates carregados por ID e versão.', 'BACKEND/app/services/t4/flow.py'],
  ['Contexto e correção', 'Base autorizada do T2, contexto selecionado por tarefa e campo de correção que substitui a pergunta anterior.', 'BACKEND/knowledge/politica_aurora_tech.txt'],
  ['Validação e recuperação', 'Contrato JSON do roteador, campos do especialista e uma repetição no máximo por execução. Factualidade revisada por uma pessoa.', 'BACKEND/tests/test_t4_flow.py'],
  ['13 casos e evidências', 'Catálogo disponível na aba Testes. Executar, revisar e exportar CSV/JSON; a entrega depende de salvar esses resultados.', 'tests/casos.csv + tests/resultados.csv + evidencias/'],
  ['Comparação com T2', 'Reaplicar R1–R5 e L1–L2, avaliar e transferir as métricas para o relatório. Não há resultado presumido.', 'evaluation/comparacao_baseline.md'],
];

export default function DeliveryPanel({ config }: { config: FlowConfig | null }) {
  return <section className="t4-delivery" aria-labelledby="delivery-heading">
    <span className="eyebrow">Rastreabilidade da entrega</span><h2 id="delivery-heading">Como o projeto atende ao Trabalho 4</h2><p className="t4-lead">Cada requisito tem um comportamento demonstrável e um artefato no repositório. O fechamento da entrega depende das evidências de execução.</p>
    <div className="t4-continuity">{[
      ['01', 'Escolher o modelo', 'Modelo selecionado pelo ambiente do backend.'],
      ['02', 'Definir a referência', 'Copiloto RH · sete casos · factualidade de 71,43%.'],
      ['03', 'Versionar os prompts', 'TRH-01 v0.3 e TRH-02/03/04 v0.1.'],
      ['04', 'Integrar e demonstrar', 'Roteamento, contexto, validação e recuperação de falhas.'],
    ].map(([number, title, text]) => <article key={number}><span>T{number}</span><h3>{title}</h3><p>{text}</p></article>)}</div>
    <div className="t4-table-wrap"><table className="t4-table"><caption>Mapa de requisitos e artefatos</caption><thead><tr><th>Requisito</th><th>Evidência na aplicação</th><th>Artefato</th></tr></thead><tbody>{requirements.map(([title, description, file]) => <tr key={title}><th scope="row">{title}</th><td>{description}</td><td><code>{file}</code></td></tr>)}</tbody></table></div>
    <div className="t4-delivery-notes"><section><h3>Antes de entregar</h3><ul><li>Executar os 13 casos e registrar a revisão humana.</li><li>Reaplicar e comparar os sete casos do baseline.</li><li>Exportar as evidências e adicioná-las ao pacote/repositório.</li><li>Conferir os templates reconstruídos com os originais do T3.</li><li>Conferir o modelo configurado e registrar mudanças de configuração nas evidências.</li></ul></section><section><h3>Limites conhecidos</h3><p>{config?.prompt_provenance ?? 'Conferência dos templates com os originais do T3 pendente.'}</p><p>A validação automática verifica contratos de saída, não a veracidade de cada afirmação. A aprovação de exceções e decisões individuais permanece com RH/diretoria.</p><p>O chat RAG e os uploads são recursos complementares. O fluxo T4 usa a política versionada para manter os testes reproduzíveis.</p></section></div>
    <footer className="t4-academic-footer">PUC Minas · IA Generativa e Aplicações com LLMs<br />Geração de Linguagem Natural e Engenharia de Prompt · Prof. Ricardo Brito Alves<br />Dayvson Pellegrino Rodrigues · Denilson Bremer Procopio Ribeiro · Leonardo Mello Ragagnin</footer>
  </section>;
}
