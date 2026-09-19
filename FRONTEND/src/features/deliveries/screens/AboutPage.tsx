import AcademicFooter from '../components/AcademicFooter';
import { academicProject } from '../utils/academicProject';
import { pagePaths } from '../utils/catalogue';

export default function AboutPage() {
  return <article className="delivery-page about-page">
    <header className="about-hero">
      <div><span className="eyebrow">Sobre · Projeto acadêmico</span><h1>Conhecimento aplicado.<br /><em>Um trabalho em grupo.</em></h1><p>Este site apresenta a construção de um Copiloto Inteligente Corporativo para o caso Aurora Tech, desenvolvido na disciplina de {academicProject.subject}.</p></div>
      <aside className="about-academic-card" aria-label="Contexto acadêmico"><span className="eyebrow">{academicProject.institution}</span><h2>{academicProject.course}</h2><p>{academicProject.subject}</p><span className="about-label">Professor</span><strong>{academicProject.professor}</strong></aside>
    </header>
    <section className="about-team" aria-labelledby="participants-heading"><div className="delivery-section-heading"><div><span className="eyebrow">Quem construiu este projeto</span><h2 id="participants-heading">Integrantes do grupo</h2></div><p>Autoria das entregas deste projeto.</p></div><ul className="about-participants">{academicProject.participants.map((name, index) => <li key={name}><span className="about-member-number" aria-hidden="true">0{index + 1}</span><h3>{name}</h3><p>Integrante do grupo</p></li>)}</ul></section>
    <section className="about-purpose" aria-labelledby="about-purpose-heading"><div><span className="eyebrow">O trabalho</span><h2 id="about-purpose-heading">Da experimentação<br />à aplicação com LLMs.</h2></div><div><p>O projeto investiga como modelos de linguagem e técnicas de engenharia de prompt podem apoiar consultas à política de trabalho híbrido da Aurora Tech. O copiloto de RH auxilia colaboradores e gestores a entender regras, verificar elegibilidade e obter orientações de segurança a partir de uma base autorizada.</p><p>As entregas documentam essa evolução: comparação de modelos e prompts (T1), especificação e baseline (T2), biblioteca de prompts versionados (T3) e integração em um fluxo de geração com protótipo textual (T4).</p><p>O portal reúne os relatórios, as decisões, os resultados e as pendências para facilitar a leitura e a correção do professor. O frontend apresenta as evidências e o backend executa o fluxo demonstrado no Trabalho 4.</p></div></section>
    <aside className="delivery-notice"><strong>Finalidade acadêmica e limites do protótipo</strong><p>O modelo de geração adotado é Mistral Large (mistralai/mistral-large), escolhido no Trabalho 1 e mantido nas entregas seguintes, no fluxo T4 e no chat RAG. Mistral Embed é usado separadamente na busca de documentos, não para gerar respostas.</p><p>Esta aplicação é uma demonstração acadêmica, não um canal oficial de atendimento de RH. Não aprova exceções nem toma decisões individuais. Resultados históricos e simulações são identificados; a avaliação factual e a aprovação das evidências exigem revisão humana.</p></aside>
    <div className="about-actions"><a className="delivery-button delivery-button--primary" href={pagePaths.overview}>Conhecer as entregas →</a><a className="delivery-button" href={pagePaths.t4}>Abrir o protótipo do T4 ↗</a></div>
    <AcademicFooter />
  </article>;
}
