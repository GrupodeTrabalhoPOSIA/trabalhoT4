import { useRef, useState } from 'react';
import MarkdownContent from '@/features/chat/components/MarkdownContent';
import { downloadText } from '@/common/download';
import { candidate, cases, categories } from './data';
import { casesCsv, firstRuns, metrics, resultsCsv } from './evaluation';
import { useT5 } from './useT5';
import type { Case, Category } from './types';
import EvaluationPanel from './EvaluationPanel';
import DeliveryPanel from './DeliveryPanel';
import '@/styles/t5.css';

type Tab = 'prototype' | 'cases' | 'evaluation' | 'delivery';
export default function T5Page() {
  const [tab, setTab] = useState<Tab>('prototype');
  const [question, setQuestion] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [activeCase, setActiveCase] = useState<Case>();
  const [selectedId, setSelectedId] = useState('');
  const [loadingCase, setLoadingCase] = useState(false);
  const [fileError, setFileError] = useState('');
  const [filter, setFilter] = useState<Category | 'all'>('all');
  const input = useRef<HTMLInputElement>(null);
  const { config, configError, runs, reviews, setReviews, busy, error, execute, assess } = useT5();
  const selected = runs.find(r => r.execution_id === selectedId);
  const values = metrics(runs, config?.model);
  const ready = Boolean(config?.model?.trim()) && config?.candidate === candidate;
  const locked = busy || loadingCase;
  const simulation = activeCase && activeCase.mode !== 'real';

  async function loadCase(value: Case) {
    setLoadingCase(true); setFileError(''); setSelectedId(''); setActiveCase(undefined); setFile(null); setQuestion(value.question); setTab('prototype');
    if (input.current) input.current.value = '';
    try {
      if (value.fixture) {
        const response = await fetch(`/entregas/t5/${value.fixture}`);
        if (!response.ok || !response.headers.get('content-type')?.includes('pdf')) throw new Error('Arquivo de teste indisponível. Confira a publicação dos PDFs do T5.');
        setFile(new File([await response.blob()], value.fixture, { type: 'application/pdf' }));
      }
      setActiveCase(value);
    } catch (reason) { setFileError(reason instanceof Error ? reason.message : 'Não foi possível preparar o caso.'); }
    finally { setLoadingCase(false); }
  }
  function exportEvidence() {
    downloadText('evidencias_t5_v1.json', JSON.stringify({ candidate, exported_at: new Date().toISOString(), config, cases, runs, reviews }, null, 2), 'application/json');
  }

  return <div className="t4-page t5-page">
    <header className="t4-hero"><div><span className="t4-kicker"><span>TRABALHO 05</span> Copiloto Inteligente Corporativo</span><h1>Protótipo multimodal<br /><em>e plano de avaliação.</em></h1><p>Da política anexada à resposta com evidências. Uma nova modalidade, o mesmo copiloto de RH e critérios explícitos para avaliar qualidade e segurança.</p></div><div className="t4-hero-note"><span className="t4-pulse-dot" /> CANDIDATA EM AVALIAÇÃO<strong>T1 → T2 → T3 → T4 → <span>T5</span></strong><small>Documentos + perguntas<br />Fontes, testes e revisão humana.</small></div></header>
    <div className="t4-overview"><div><span>Modalidade</span><strong>Documento + texto</strong></div><div><span>Versão da candidata</span><strong>{config?.candidate ?? 't5-v1 · aguardando API'}</strong></div><div><span>Casos nesta sessão</span><strong>{values.count} / 20 executados</strong></div><div><span>Decisão preliminar</span><strong>Aguardando avaliação humana</strong></div></div>
    {configError && <p className="t4-notice" role="status">A configuração do Trabalho 5 está indisponível. Publique o backend com as rotas /t5 e recarregue a página. O plano de avaliação e o catálogo continuam disponíveis.</p>}
    {config && !ready && <p className="t4-notice" role="alert">A API precisa confirmar t5-v1 e o modelo configurado para executar esta candidata.</p>}
    <nav className="t4-tabs" aria-label="Seções do Trabalho 5">{([['prototype', '01', 'Protótipo multimodal'], ['cases', '02', 'Testes e evidências'], ['evaluation', '03', 'Métricas e rubrica'], ['delivery', '04', 'Riscos e entrega']] as const).map(([id, number, label]) => <button key={id} className={`t4-tab${tab === id ? ' t4-tab--active' : ''}`} aria-current={tab === id ? 'page' : undefined} onClick={() => setTab(id)}><span>{number}</span>{label}</button>)}</nav>
    <div hidden={tab !== 'prototype'} className="t4-workspace"><div className="t4-main-column">
      <section className="t4-input-panel"><span className="eyebrow">Uma política, uma pergunta, evidências</span><h2>Consulte um documento</h2><p className="t4-muted">Anexe uma política para responder com base nela. Sem arquivo, o copiloto usa a política textual do Trabalho 4.</p>
        <div className="t4-example-buttons"><button disabled={locked} onClick={() => void loadCase(cases.find(c => c.id === 'M1')!)}>Experimentar PDF de exemplo</button><button disabled={locked} onClick={() => void loadCase(cases.find(c => c.id === 'M5')!)}>Testar injeção no documento</button><button disabled={locked} onClick={() => void loadCase(cases[0])}>Usar modo textual</button></div>
        <form onSubmit={e => { e.preventDefault(); setSelectedId(''); void execute(question, file, activeCase).then(id => { if (id) setSelectedId(id); }); }}>
          <div className={`t5-upload${file ? ' t5-upload--selected' : ''}`}><span className="t5-file-icon" aria-hidden="true">↥</span><div><label htmlFor="t5-file">{file ? file.name : 'Anexar política corporativa'}</label><p>PDF com texto, DOCX, TXT ou Markdown · até 10 MB</p><input id="t5-file" ref={input} type="file" accept=".pdf,.docx,.txt,.md" disabled={locked || Boolean(simulation)} onChange={e => { setFile(e.target.files?.[0] ?? null); setActiveCase(undefined); setSelectedId(''); setFileError(''); }} />{file && <button type="button" className="t4-text-button" disabled={locked} onClick={() => { setFile(null); setActiveCase(undefined); setSelectedId(''); if (input.current) input.current.value = ''; }}>Remover anexo</button>}</div></div>
          <p className="t4-input-hint">Somente documentos sintéticos, públicos ou anonimizados. O anexo não é salvo na base compartilhada. PDFs digitalizados precisam de uma versão com texto.</p>
          <label htmlFor="t5-question">Pergunta sobre a política</label><textarea id="t5-question" value={question} onChange={e => { setQuestion(e.target.value); setActiveCase(undefined); setSelectedId(''); }} disabled={locked || Boolean(simulation)} maxLength={2000} rows={4} placeholder="Ex.: Quais são os requisitos para trabalhar remotamente?" required />
          {activeCase && <div className="t4-case-context"><strong>{activeCase.id} · {categories[activeCase.category]}</strong><p>Esperado: {activeCase.expected}</p>{simulation && <p className="t4-warning">Simulação técnica determinística. Não mede qualidade nem latência do modelo.</p>}</div>}
          <div className="t4-form-actions"><span className="t5-mode">{file ? '◉ Documento + texto' : '○ Somente texto'}</span><button className="primary-button" disabled={locked || !ready || !question.trim() || Boolean(fileError)}>{busy ? 'Executando…' : loadingCase ? 'Preparando arquivo…' : simulation ? 'Executar simulação →' : 'Consultar política →'}</button></div><p className="t4-input-hint">{config?.model ?? 'Aguardando configuração do modelo'} · chamadas reais podem consumir créditos OpenRouter.</p>
        </form>
      </section>
      {(error || fileError) && <p className="t4-error" role="alert">{fileError || error}</p>}
      {busy && <div className="t4-loading" role="status"><span className="page-loader__indicator" />Processando a entrada e executando o fluxo. O resultado será registrado ao concluir.</div>}
      {selected && !busy ? <section className="t4-result"><div className="t4-result-heading"><span className="t4-pill">{selected.status.replaceAll('_', ' ')}</span><small>{selected.mode === 'real' ? 'Execução real' : 'Simulação técnica'}</small></div><h2>Resposta e fundamentação</h2><MarkdownContent content={selected.answer} /><dl className="t4-run-metrics"><div><dt>Prompt</dt><dd>{selected.prompt_id} {selected.prompt_version}</dd></div><div><dt>Latência total</dt><dd>{(selected.latency_ms / 1000).toFixed(2)} s</dd></div><div><dt>Trechos recuperados</dt><dd>{selected.sources.length}</dd></div><div><dt>Validação automática</dt><dd>{selected.valid ? 'Contrato aceito' : 'Rejeição / falha'}</dd></div></dl>
        <p className="t4-muted">{selected.expected} A validação de formato e a similaridade dos trechos não comprovam factualidade.</p>
        {selected.document && <p className="t4-muted">{selected.document.quality}</p>}
        {selected.sources.map(s => <details className="t4-details" key={s.chunk_index}><summary>{s.document_name} · {s.page ? `pág. ${s.page} · ` : ''}trecho {s.chunk_index + 1}</summary><blockquote>{s.content}</blockquote><small className="t5-hash">SHA-256: {s.document_hash}</small><p className="t4-muted">Similaridade: {s.relevance.toFixed(3)} · não é probabilidade de resposta correta.</p></details>)}
        <div className="t5-two-columns">{(['success', 'critical'] as const).map(field => <label key={field}>{field === 'success' ? 'Atendeu ao resultado esperado?' : 'Houve critério eliminatório?'}<select value={selected[field] === null ? '' : String(selected[field])} onChange={e => assess(selected.execution_id, field, e.target.value === '' ? null : e.target.value === 'true')}><option value="">Pendente · revisão humana</option><option value="true">Sim</option><option value="false">Não</option></select></label>)}</div>
        <details className="t4-details"><summary>Inspecionar registro, contexto e saídas brutas</summary><pre>{JSON.stringify(selected, null, 2)}</pre></details>
      </section> : !busy && <section className="t4-empty-result"><span aria-hidden="true">↳</span><h2>A fonte faz parte da resposta.</h2><p>Confira os trechos recuperados, a página e o resultado da validação após uma consulta.</p></section>}
    </div><aside className="t4-trace"><span className="eyebrow">Do arquivo à evidência</span><h2>O caminho do documento</h2><ol className="t4-steps">{[['Validar a entrada', 'Tipo, tamanho, páginas e texto extraível.'], ['Recuperar os trechos', 'Embeddings e busca apenas no anexo desta execução.'], ['Reutilizar os especialistas', 'Triagem e prompts versionados do Trabalho 4.'], ['Responder com fonte', 'Documento, hash, página e trecho identificável.'], ['Avaliar e registrar', 'Formato automático; qualidade e segurança por pessoas.']].map(([title, detail], i) => <li className="t4-step" key={title}><span className="t4-step-number">0{i + 1}</span><div><strong>{title}</strong><small>{detail}</small></div></li>)}</ol><div className="t4-exceptions"><strong>Limites explícitos</strong><p>Até 20 páginas em PDF.<br />Sem OCR ou leitura de imagens.<br />Sem evidência → declarar ausência.<br />Decisões de RH → revisão humana.</p></div><a className="t5-fixture-link" href="/entregas/t5/politica-v1.pdf" download>Baixar política sintética v1 ↓</a></aside></div>
    <div hidden={tab !== 'cases'} className="t5-stack"><section className="t4-input-panel"><div className="t4-section-heading"><div><span className="eyebrow">Conjunto versionado · t5-v1</span><h2>20 casos, três perspectivas</h2></div><button className="delivery-button" onClick={() => downloadText('casos_v1.csv', casesCsv(), 'text/csv;charset=utf-8')}>Baixar casos ↓</button></div><p className="t4-muted">13 casos herdados do T4 e 7 documentais. E1/E2 cobrem recuperação técnica por simulação. Cada caso carrega sua pergunta e, quando necessário, um PDF sintético. Alterar a entrada transforma a execução em livre.</p><div className="t5-category-cards">{(Object.keys(categories) as Category[]).map(category => <div key={category}><strong>{cases.filter(c => c.category === category).length.toString().padStart(2, '0')}</strong><span>{categories[category]}</span></div>)}</div>
      <label className="t5-filter">Filtrar categoria<select value={filter} onChange={e => setFilter(e.target.value as Category | 'all')}><option value="all">Todos os 20 casos</option>{Object.entries(categories).map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></label>
      <div className="t4-table-scroll" role="region" aria-label="Tabela com rolagem horizontal" tabIndex={0}><table className="t4-table"><caption>Casos e primeira execução da candidata</caption><thead><tr><th>Caso</th><th>Entrada e critério</th><th>Modalidade</th><th>Resultado</th><th>Ação</th></tr></thead><tbody>{cases.filter(c => filter === 'all' || c.category === filter).map(c => { const run = firstRuns(runs, config?.model).find(r => r.case_id === c.id); return <tr key={c.id}><th>{c.id}<small className="t5-table-detail">{categories[c.category]}</small></th><td>{c.question}<small className="t5-table-detail">{c.expected}</small></td><td>{c.fixture ? <a href={`/entregas/t5/${c.fixture}`} download>PDF v1 ↓</a> : c.mode !== 'real' ? 'Simulação' : 'Texto'}</td><td>{!run ? 'Não executado' : run.success === null ? 'Revisão pendente' : run.success ? 'Atendeu' : 'Não atendeu'}</td><td><button className="t4-text-button" disabled={locked} onClick={() => void loadCase(c)}>Carregar {c.id} →</button>{run && <button className="t4-text-button" onClick={() => { setSelectedId(run.execution_id); setTab('prototype'); }}>Ver resultado</button>}</td></tr>; })}</tbody></table></div>
    </section><section className="t4-input-panel"><h2>Histórico e exportação</h2><p className="t4-muted">As evidências permanecem ao navegar entre entregas, mas se perdem ao fechar ou recarregar a página. Exporte antes de sair. Todas as tentativas são mantidas; as métricas usam a primeira execução de cada caso.</p><div className="t4-example-buttons"><button disabled={!runs.length} onClick={() => downloadText('resultados_v1.csv', resultsCsv(runs), 'text/csv;charset=utf-8')}>Exportar resultados CSV ↓</button><button disabled={!runs.length} onClick={exportEvidence}>Exportar evidências JSON ↓</button></div><div className="t4-run-history">{runs.map(r => <button key={r.execution_id} onClick={() => { setSelectedId(r.execution_id); setTab('prototype'); }}><strong>{r.case_id}</strong><span>{r.status.replaceAll('_', ' ')}</span><small>{new Date(r.executed_at).toLocaleString('pt-BR')} · {r.mode === 'real' ? 'real' : 'simulação'}</small></button>)}</div>{!runs.length && <p className="t4-muted">Nenhuma execução registrada nesta sessão.</p>}</section></div>
    <div hidden={tab !== 'evaluation'}><EvaluationPanel model={config?.model} runs={runs} reviews={reviews} onReview={review => setReviews(previous => [...previous, review])} /></div>
    <div hidden={tab !== 'delivery'}><DeliveryPanel model={config?.model} runs={runs} reviews={reviews} /></div>
    <p className="t4-footnote">Protótipo acadêmico · documentos sintéticos · avaliação humana independente · nenhuma aprovação presumida.</p>
  </div>;
}
