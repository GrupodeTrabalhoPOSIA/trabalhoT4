import AcademicFooter from '../components/AcademicFooter';
import { pagePaths, reports, type ReportId } from '../utils/catalogue';

export default function ReportPage({ id }: { id: ReportId }) {
  const report = reports[id];
  const number = Number(id.slice(1));
  const next = number === 1 ? 't2' : number === 2 ? 't3' : 't4';
  return <article className="delivery-page delivery-report">
    <a className="delivery-back" href={pagePaths.overview}>← Todas as entregas</a>
    <header className="delivery-report-hero"><div><span className="eyebrow">Trabalho 0{number} · Relatório disponível</span><h1>{report.title}</h1><p>{report.subtitle}</p></div><a className="delivery-button" href={report.source.href} download>↓ {report.source.label}</a></header>
    <p className="delivery-source-note">Síntese do relatório entregue pelo grupo. Os números abaixo são históricos, não execuções realizadas neste site.</p>
    <dl className="delivery-metrics">{report.metrics.map(metric => <div key={metric.label}><dt>{metric.label}</dt><dd>{metric.value}</dd><small>{metric.detail}</small></div>)}</dl>
    <div className="delivery-report-intro"><section><span className="eyebrow">01 · Propósito e método</span><h2>O que esta entrega demonstra</h2><p>{report.objective}</p><ul className="delivery-method">{report.method.map(item => <li key={item}>{item}</li>)}</ul></section><aside className="delivery-checkpoints"><span className="eyebrow">Roteiro de correção</span><h2>Onde concentrar a leitura</h2><ol>{report.checkpoints.map(item => <li key={item}>{item}</li>)}</ol><p>Confira os registros completos no relatório original ao final da página.</p></aside></div>
    <section aria-labelledby={`${id}-evidence-heading`}><div className="delivery-section-heading"><div><span className="eyebrow">02 · Evidências registradas</span><h2 id={`${id}-evidence-heading`}>Resultados, sem esconder as lacunas</h2></div></div>
      {report.tables.map(table => <div className="delivery-table-wrap" key={table.title} tabIndex={0} role="region" aria-label={table.title}><table className="delivery-table"><caption>{table.title}</caption><thead><tr>{table.columns.map(column => <th key={column} scope="col">{column}</th>)}</tr></thead><tbody>{table.rows.map(row => <tr key={row[0]}>{row.map((cell, index) => index === 0 ? <th key={index} scope="row">{cell}</th> : <td key={index}>{cell}</td>)}</tr>)}</tbody></table></div>)}
    </section>
    <div className="delivery-conclusions"><section><span className="eyebrow">03 · Decisão e continuidade</span><h2>O que levamos adiante</h2><p>{report.decision}</p><div className="delivery-handoff"><span aria-hidden="true">↳</span><p>{report.handoff}</p></div></section><section><span className="eyebrow">04 · Leitura crítica</span><h2>Limites e pendências</h2><ul>{report.limitations.map(item => <li key={item}>{item}</li>)}</ul></section></div>
    <section className="delivery-source" aria-labelledby={`${id}-source-heading`}><div><span className="eyebrow">Fonte desta página</span><h2 id={`${id}-source-heading`}>Consulte a entrega original</h2><p>{report.source.original}</p><small>Cópia do arquivo fornecido em entregas/, sem alteração do conteúdo.</small></div><a className="delivery-button" href={report.source.href} download>Baixar relatório original ↓</a></section>
    <nav className="delivery-pagination" aria-label="Sequência das entregas"><a href={pagePaths[number === 1 ? 'overview' : number === 2 ? 't1' : 't2']}>← {number === 1 ? 'Visão geral' : `Trabalho ${number - 1}`}</a><a href={pagePaths[next]}>Continuar no Trabalho {number + 1} →</a></nav>
    <AcademicFooter />
  </article>;
}
