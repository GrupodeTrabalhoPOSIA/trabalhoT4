import AcademicFooter from '../components/AcademicFooter';
import { deliveries, pagePaths } from '../utils/catalogue';

export default function OverviewPage() {
  return <div className="delivery-page">
    <header className="portal-hero">
      <div><span className="eyebrow">Portfólio acadêmico · Entregas 01—05</span><h1>Um copiloto.<br /><em>Uma construção em etapas.</em></h1><p>Da escolha do modelo ao fluxo executável: acompanhe as decisões, os resultados e as evidências do copiloto de RH da Aurora Tech.</p><a className="delivery-button delivery-button--primary" href={pagePaths.t5}>Experimentar o Trabalho 5 <span aria-hidden="true">↗</span></a></div>
      <aside className="portal-guide" aria-labelledby="guide-title"><span className="eyebrow">Para quem avalia</span><h2 id="guide-title">O percurso está aqui.</h2><ol><li><strong>Entenda a decisão</strong><span>Objetivo e método de cada trabalho.</span></li><li><strong>Confira a evidência</strong><span>Resultados históricos e relatórios originais.</span></li><li><strong>Inspecione o protótipo</strong><span>Execute o T5 e confira suas fontes e avaliações.</span></li></ol></aside>
    </header>
    <section aria-labelledby="deliveries-heading"><div className="delivery-section-heading"><div><span className="eyebrow">Linha de evolução</span><h2 id="deliveries-heading">As entregas do projeto</h2></div><p>Cada etapa deixa uma base para a próxima.</p></div>
      <div className="delivery-cards">{deliveries.map(delivery => <a className={`delivery-card${delivery.id === 't5' ? ' delivery-card--current' : ''}`} href={pagePaths[delivery.id]} key={delivery.id} aria-label={`Abrir Trabalho ${Number(delivery.number)}: ${delivery.title}`}>
        <div className="delivery-card-top"><span className="delivery-number">{delivery.number}</span><span className="delivery-tag">{delivery.status}</span></div>
        <p className="delivery-card-verb">{delivery.verb}</p><h3>{delivery.title}</h3><p className="delivery-card-description">{delivery.description}</p><small>{delivery.evidence}</small><div className="delivery-card-bottom"><span>Ver entrega</span><span aria-hidden="true">↗</span></div>
      </a>)}</div>
    </section>
    <section className="portal-context" aria-labelledby="context-title"><div><span className="eyebrow">O mesmo caso, do início ao fim</span><h2 id="context-title">RH da Aurora Tech.<br />Política de trabalho híbrido.</h2><p>Um assistente para colaboradores e gestores consultarem regras, elegibilidade e segurança. A base autorizada delimita as respostas; decisões individuais continuam com as pessoas responsáveis.</p></div><div className="portal-handoffs">{deliveries.map(delivery => <div key={delivery.id}><span>T{Number(delivery.number)}</span><p>{delivery.outcome}</p></div>)}</div></section>
    <aside className="delivery-notice"><strong>Transparência sobre as evidências</strong><p>As páginas T1–T3 sintetizam os relatórios fornecidos pelo grupo, sem reexecutar os experimentos. Pendências continuam identificadas. T4 e T5 são interativos e sua validação final depende das execuções, da revisão humana e da exportação dos resultados.</p></aside>
    <AcademicFooter />
  </div>;
}
