# Arquitetura consolidada — Aurora Tech

## Problema, usuários e fronteira
Colaboradores e gestores consultam a política de trabalho híbrido para explicar regras, verificar elegibilidade e orientar segurança. O copiloto não decide casos individuais nem aprova exceções. A autoridade permanece com o RH.

## Componentes e percurso
1. Interface React/TypeScript: catálogo T1–T6, execução, fontes, revisão humana, importação/exportação e rascunho local no navegador.
2. FastAPI: contratos de entrada, catálogo fechado de vinte casos e seis cenas, manifesto e auditoria do gate.
3. Contexto: política textual versionada; anexos PDF/DOCX/TXT/MD passam por validação de extensão, limite de tamanho e extração. PDFs limitados a vinte páginas, pelo menos quarenta caracteres de texto e até trinta mil caracteres em trechos. Não há OCR.
4. Recuperação multimodal documental: embeddings e similaridade por cosseno, limiar, top-k e orçamento de contexto. Trechos e hashes acompanham a saída. Documentos T5/T6 existem apenas durante a requisição. O chat RAG complementar usa Supabase, mas não recebe os ataques do conjunto de testes.
5. Orquestração: TRH-04 v0.1 seleciona TRH-01 v0.3 (regras), TRH-02 v0.1 (elegibilidade) ou TRH-03 v0.1 (segurança). O modelo de geração vem do ambiente; configuração exata consta no manifesto. Sem troca automática de modelo.
6. Validação: JSON do roteador, contexto necessário e contrato da resposta. Uma repetição controlada corrige formato; persistindo falha, fallback seguro. Ambiguidade pede esclarecimento. Falhas do provedor são reportadas, sem inventar evidência.
7. Observabilidade: logs técnicos de rota, duração e status; resultados registram IDs, configuração, latência, tentativas, fontes e modalidade. Logs não devem conter corpos de documentos ou credenciais. O navegador guarda evidências declaradas; exporte o JSON como cópia de segurança.
8. Segurança e revisão: documentos são dados não confiáveis separados das instruções; revisão factual e de segurança é humana. Dois avaliadores independentes pontuam dez casos. Um responsável decide o gate após conferir riscos e evidências.

## Decisões e alternativas rejeitadas
**Recuperar trechos em vez de enviar sempre o documento inteiro.** Permite rastrear página e trecho e limitar contexto. A alternativa simples de envio integral aumenta tokens, dificulta localizar evidência e pode diluir instruções. Limite residual: similaridade não garante relevância factual nem cobertura completa.

**Isolar anexos por requisição em vez de indexar a avaliação adversarial na coleção compartilhada.** Preserva o contexto de cada teste e evita contaminar consultas de outros usuários. A coleção compartilhada seria adequada a um acervo corporativo governado, mas exige ingestão, autorização e exclusão controladas.

**Manter revisão humana em vez de aprovar pelo esquema válido.** Uma resposta bem formatada ainda pode inventar uma regra. A automação verifica a correspondência dos artefatos e a completude das declarações; não autentica pessoas nem a origem de um JSON importado.

## Versão e limites
O SHA-256 do manifesto identifica código, prompts, base, parâmetros, entradas e casos. O runtime verifica seus arquivos e parâmetros; a interface exige o mesmo identificador. Alterações exigem novo congelamento e reexecução dos vinte casos. A configuração do provedor é declarada; o identificador público do modelo não fixa os pesos internos do serviço externo. Dependências Python possuem faixas de versão e exigem validação no ambiente de reprodução.

Não há autenticação corporativa, trilha de auditoria persistente autenticada, OCR, coleta automática de custos nem aprovação para produção. Os prompts foram reconstruídos dos relatórios e precisam ser conferidos com os originais do T3. Resultados acadêmicos não autorizam operação real.
