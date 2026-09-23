import { useRef, useState } from 'react';
import DeliveryPanel from '../components/DeliveryPanel';
import EvidencePanel from '../components/EvidencePanel';
import FlowTrace from '../components/FlowTrace';
import RunResult from '../components/RunResult';
import { useT4 } from '../hooks/useT4';
import { categoryLabels, testCases } from '../utils/cases';
import type { TestCase } from '../utils/types';

type Tab = 'prototype' | 'evidence' | 'delivery';

export default function T4Page() {
  const [tab, setTab] = useState<Tab>('prototype');
  const [question, setQuestion] = useState('');
  const [correction, setCorrection] = useState('');
  const [showCorrection, setShowCorrection] = useState(false);
  const [testCase, setTestCase] = useState<TestCase>();
  const correctionRef = useRef<HTMLTextAreaElement>(null);
  const { config, configError, runs, busy, error, execute, review, selected, setSelectedId } = useT4();
  const count = testCases.filter(c => runs.some(r => r.case_id === c.id)).length;
  const realModelReady = Boolean(config?.model?.trim());
  const simulation = testCase?.mode !== undefined && testCase.mode !== 'real';

  function loadCase(value: TestCase) {
    setTestCase(value); setQuestion(value.question); setCorrection(''); setShowCorrection(false);
    setSelectedId(null); setTab('prototype');
  }

  return <div className="t4-page">
    <header className="t4-hero"><div><span className="t4-kicker"><span>TRABALHO 04</span> Copiloto Inteligente Corporativo</span><h1>Fluxo de geração<br /><em>e protótipo textual.</em></h1><p>Copiloto de RH da Aurora Tech. Uma pergunta percorre triagem, contexto, prompt especialista e validação — com cada decisão disponível para inspeção.</p></div><div className="t4-hero-note"><span className="t4-pulse-dot" /> PROJETO INCREMENTAL<strong>T1 → T2 → T3 → <span>T4</span></strong><small>Biblioteca de prompts conectada<br />a um fluxo executável.</small></div></header>
    <div className="t4-overview"><div><span>Escopo</span><strong>Política de trabalho híbrido</strong></div><div><span>Modelo configurado</span><strong>{config?.model ?? (configError ? 'Configuração indisponível' : 'Carregando…')}</strong></div><div><span>Templates versionados</span><strong>{config ? Object.keys(config.prompts).length : '—'} prompts · 3 especialistas</strong></div><div><span>Evidências nesta sessão</span><strong>{count} / 13 casos executados</strong></div></div>
    {configError && <p className="t4-notice" role="status">Não foi possível carregar a configuração T4. Confira se o backend com as rotas /t4 já foi publicado e recarregue a página. As execuções abaixo também dependem desse deploy.</p>}
    <p className="t4-muted">O modelo executado é definido por OPENROUTER_MODEL no backend.</p>
    {config && !realModelReady && <p className="t4-notice" role="alert">O backend ainda não informou o modelo configurado. Configure OPENROUTER_MODEL e recarregue esta página.</p>}
    <nav className="t4-tabs" aria-label="Seções do Trabalho 4">{([['prototype', '01', 'Protótipo'], ['evidence', '02', 'Testes e evidências'], ['delivery', '03', 'Mapa da entrega']] as const).map(([id, number, label]) => <button key={id} type="button" aria-current={tab === id ? 'page' : undefined} className={tab === id ? 't4-tab t4-tab--active' : 't4-tab'} onClick={() => setTab(id)}><span>{number}</span>{label}</button>)}</nav>
    {tab === 'prototype' && <div className="t4-workspace"><div className="t4-main-column">
      <section className="t4-input-panel" aria-labelledby="question-heading"><div className="t4-panel-heading"><span className="eyebrow">Entrada do fluxo</span><h2 id="question-heading">Experimente uma pergunta</h2><p className="t4-muted">Explique uma regra, verifique elegibilidade ou peça orientação de segurança.</p></div>
        <div className="t4-example-buttons">{testCases.filter(c => ['P1', 'P3', 'P4', 'D1'].includes(c.id)).map(c => <button key={c.id} type="button" disabled={busy} onClick={() => loadCase(c)}>{({ P1: 'Dias remotos', P3: 'Elegibilidade', P4: 'Segurança', D1: 'Dado ausente' })[c.id]}</button>)}</div>
        <form onSubmit={e => { e.preventDefault(); void execute(question.trim(), correction.trim(), testCase); }}>
          <label htmlFor="t4-question">Pergunta ao copiloto</label><textarea id="t4-question" rows={4} maxLength={2000} disabled={busy || (testCase?.mode !== undefined && testCase.mode !== 'real')} value={question} placeholder="Ex.: Trabalho em laboratório. Sou elegível ao trabalho híbrido?" onChange={e => { setQuestion(e.target.value); setTestCase(undefined); setSelectedId(null); }} required />
          {testCase && <div className="t4-case-context"><strong>{testCase.id} · {categoryLabels[testCase.category]}</strong><p>Esperado: {testCase.expected}</p>{testCase.mode !== 'real' && <p className="t4-warning">Simulação determinística de falha. Não chama OpenRouter e não mede a qualidade do modelo.</p>}</div>}
          {showCorrection && <div className="t4-correction"><label htmlFor="t4-correction">Pergunta corrigida ou complementada</label><textarea id="t4-correction" ref={correctionRef} value={correction} maxLength={2000} rows={3} disabled={busy} onChange={e => setCorrection(e.target.value)} /><p className="t4-muted">Escreva a pergunta completa com o novo contexto. Ela substituirá a anterior; a execução será registrada como pergunta livre.</p></div>}
          <div className="t4-form-actions"><button type="button" className="t4-text-button" disabled={busy} onClick={() => { setQuestion(''); setTestCase(undefined); setCorrection(''); setShowCorrection(false); setSelectedId(null); }}>Nova pergunta</button><button type="submit" className="primary-button" disabled={busy || !question.trim() || (!simulation && !realModelReady)}>{busy ? 'Executando fluxo…' : simulation ? 'Executar simulação →' : 'Executar fluxo →'}</button></div>
          <p className="t4-input-hint">{simulation ? 'Saídas de teste serão identificadas como simuladas na exportação.' : 'Usa o modelo informado pelo backend e pode consumir créditos OpenRouter.'}</p>
        </form>
      </section>
      {busy && <div className="t4-loading" role="status"><span className="page-loader__indicator" />Classificando a pergunta e executando o fluxo. Aguarde; pode haver uma repetição controlada.</div>}
      {error && <div className="t4-error" role="alert">{error}</div>}
      {selected && !busy ? <RunResult configuredModel={config?.model} run={selected} onReview={review} onCorrect={() => { setQuestion(selected.effective_question); setTestCase(undefined); setCorrection(''); setShowCorrection(true); setTimeout(() => correctionRef.current?.focus(), 0); }} /> : !busy && <section className="t4-empty-result"><span aria-hidden="true">↳</span><h2>A execução deixa um rastro.</h2><p>A resposta, a rota escolhida, a versão do prompt e os resultados da validação aparecerão aqui.</p></section>}
      <details className="t4-policy t4-details"><summary>Base autorizada e biblioteca de prompts</summary><p>Fonte: política-piloto da Aurora Tech, herdada do T2. O fluxo não consulta os uploads da base RAG.</p><pre>{config?.knowledge_base ?? 'Aguardando configuração do backend.'}</pre><ul>{Object.entries(config?.prompts ?? {}).map(([id, version]) => <li key={id}><strong>{id} {version}</strong> · {({ 'TRH-01': 'Explicar regras', 'TRH-02': 'Verificar elegibilidade', 'TRH-03': 'Orientar segurança', 'TRH-04': 'Triagem e roteamento JSON' })[id]}</li>)}</ul><p className="t4-muted">{config?.prompt_provenance}</p></details>
    </div><FlowTrace result={busy ? null : selected} busy={busy} /></div>}
    {tab === 'evidence' && <EvidencePanel baselineModel={config?.baseline_model} runs={runs} busy={busy} onLoad={loadCase} onInspect={id => { setSelectedId(id); setTab('prototype'); }} />}
    {tab === 'delivery' && <DeliveryPanel config={config} />}
    <p className="t4-footnote">Protótipo acadêmico · decisões de RH exigem validação humana · resultados não são presumidos.</p>
  </div>;
}
