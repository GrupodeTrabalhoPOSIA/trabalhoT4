# Aurora Tech Chatbot

## Trabalho 5 — Protótipo Multimodal e Plano de Avaliação

Abra `/#/entregas/5` para consultar uma política anexada, executar o catálogo de
20 casos, aplicar a rubrica por dois avaliadores e exportar o gate preliminar.
A página segue o portal T1–T4 e mantém sua sessão ao navegar entre entregas.
Publique frontend **e backend**: as novas rotas são `GET /api/v1/t5/config` e
`POST /api/v1/t5/run` (multipart: `question`, `mode`, `file` opcional).

O T5 reutiliza os extratores, embeddings e especialistas do projeto. Cada anexo
é recuperado isoladamente em memória, sem inserir documentos adversariais no
Supabase. Sem arquivo, o fluxo textual do T4 permanece disponível. PDFs devem
ter texto selecionável; não há OCR. Limites: 10 MB, 20 páginas PDF e 30.000
caracteres extraídos incluindo sobreposições, com mínimo de 40 caracteres.
Consultas reais dependem de OpenRouter e consomem créditos. As simulações E1/E2
não fazem chamadas externas; falhas de entrada também não chamam o modelo.

As fixtures sintéticas e o protocolo estão em `FRONTEND/public/entregas/t5/`.
Para regenerar os PDFs, execute `python evaluation/generate_t5_fixtures.py` na
pasta BACKEND. Os testes automatizados usam dublês; não são as 20 execuções
acadêmicas e não comprovam resistência do modelo a injeção.

Na aba Testes, carregue cada caso para preparar a pergunta e seu PDF. Modificar
a entrada transforma a consulta em livre. Após executar, revise sucesso e
eliminatórios. Avalie P1, P3, F2 e M1–M7 com duas pessoas independentes; preserve
as notas e explique divergências. Exporte CSV de casos/resultados/rubrica,
JSON das evidências e JSON do gate/matriz. As notas e resultados não são
persistidos: exporte antes de recarregar ou fechar. Não há aprovação presumida.
Metas, fórmulas, privacidade e pacote final estão no
[protocolo v1](FRONTEND/public/entregas/t5/plano-avaliacao-v1.md).

MVP acadêmico de um chatbot RAG para responder perguntas sobre a empresa fictícia Aurora Tech. Os documentos são transformados em embeddings pela API do OpenRouter, persistidos no Supabase com `pgvector` e recuperados antes de cada resposta gerada por um modelo acessado pelo mesmo provedor.

O projeto não possui autenticação, perfis de usuário nem persistência de conversas. O histórico curto existe somente na página aberta no navegador.

## Arquitetura

```text
React + TypeScript
        │ HTTP /api/v1
        ▼
FastAPI ──► extração e chunking ──► OpenRouter / embeddings ──► Supabase / pgvector
   │                                                               │
   └──────────── pergunta + contexto recuperado ◄──────────────────┘
                              │
                              ▼
                       OpenRouter / LLM
```

## Requisitos

- Python 3.11 a 3.14;
- Node.js 20.19+ ou 22.12+;
- uma chave da OpenRouter para gerar embeddings e respostas;
- um projeto Supabase para armazenar documentos e embeddings;
- acesso de rede do backend ao OpenRouter e ao Session Pooler do Supabase.

## Instalação do backend

No PowerShell, a partir da raiz do projeto:

```powershell
cd BACKEND
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

No painel do Supabase, abra **SQL Editor** e execute `BACKEND/database/supabase/migrations/001_aurora_vector_store.sql` e depois `002_mistral_embeddings_1024.sql` da mesma pasta. Se a primeira migração já foi aplicada, execute somente a segunda, com a base vazia. Depois, edite `BACKEND/.env` e preencha:

```dotenv
OPENROUTER_API_KEY=sua-chave-local
SUPABASE_DB_URL=postgresql://postgres.PROJECT_REF:SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres
```

Copie a URI em **Connect → Session pooler** no painel do Supabase. Ela deve usar o host `pooler.supabase.com`, o usuário `postgres.PROJECT_REF` e a porta `5432`. Substitua o marcador pela senha do banco; caracteres especiais na senha precisam estar codificados para URL.

Não versione esse arquivo. A URI contém a senha do banco e fica somente no backend. Sem ela, as rotas de documentos e chat retornam `DATABASE_NOT_CONFIGURED`; sem a chave OpenRouter, a indexação e a consulta retornam `EMBEDDINGS_NOT_CONFIGURED`.

Inicie a API:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Verificações úteis:

- saúde: `http://localhost:8000/api/v1/health`;
- Swagger: `http://localhost:8000/docs`;
- ReDoc: `http://localhost:8000/redoc`.

## Instalação do frontend

Em outro terminal, a partir da raiz:

```powershell
cd FRONTEND
npm ci
Copy-Item .env.example .env
npm run dev
```

Acesse `http://localhost:5173`. Se o backend usar outra porta, altere `VITE_API_URL` em `FRONTEND/.env`.

## Inicialização rápida no Windows

Depois de instalar as dependências do backend e do frontend, execute na raiz:

```powershell
.\iniciar-local.bat
```

O arquivo prepara os `.env` ausentes, inicia backend e frontend em terminais separados e abre `http://localhost:5173`. Para verificar os pré-requisitos sem iniciar os servidores:

```powershell
.\iniciar-local.bat --check
```

## Uso

1. Abra **Base de conhecimento**.
2. Adicione arquivos PDF, TXT, Markdown ou DOCX, com até 10 MB.
3. Volte ao **Chat** e faça uma pergunta contida nos documentos.
4. Confira as fontes exibidas abaixo da resposta.

Quando nenhum trecho atinge o limiar de relevância, a API recusa a pergunta sem chamar o modelo. Documentos duplicados são identificados pelo hash do conteúdo.

## Endpoints principais

| Método | Rota | Função |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Verifica a API |
| `POST` | `/api/v1/documents` | Processa e indexa um documento |
| `GET` | `/api/v1/documents` | Lista documentos indexados |
| `GET` | `/api/v1/documents/{id}/content` | Retorna os trechos de texto salvos, na ordem, sem embeddings |
| `DELETE` | `/api/v1/documents/{id}` | Remove documento e chunks |
| `POST` | `/api/v1/chat` | Recupera contexto e responde |

## Configuração RAG adotada

- embeddings: `mistralai/mistral-embed-2312`, via OpenRouter, com 1024 dimensões fixas;
- chunks de 700 caracteres, com sobreposição de 100;
- até 5 trechos por busca;
- relevância mínima de 0,35;
- contexto máximo de 6.000 caracteres;
- modelo de geração: `mistralai/mistral-large`, escolhido no Trabalho 1 e mantido no chat RAG, na triagem e nos especialistas do T4.

Os parâmetros e o modelo são configurados em `BACKEND/.env` ou no ambiente do processo. `OPENROUTER_MODEL` e `OPENROUTER_EMBEDDING_MODEL` são obrigatórios e não possuem fallback no código: ausência ou valor vazio impede iniciar a API. Para este projeto, configure `OPENROUTER_MODEL=mistralai/mistral-large`. O frontend usa a configuração informada pela API. Comparações com o baseline histórico continuam identificando modelos diferentes.

O serviço valida vetores de 1024 dimensões, correspondentes ao tipo `vector(1024)` após a migração 002. O cliente não envia o parâmetro opcional de redução de dimensão ao Mistral. Trocar o modelo de **embeddings** exige reindexar todos os documentos, mesmo quando a dimensão for mantida, pois modelos diferentes geram espaços vetoriais incompatíveis. Alterar a dimensão também exige uma nova migração. Mistral Embed é usado somente na recuperação de documentos; não substitui Mistral Large na geração textual.

## Configuração em produção

### Frontend na Vercel

O repositório inclui configuração para os dois formatos de projeto aceitos pela Vercel:

- configuração recomendada no painel: **Root Directory = `FRONTEND`**;
- se a Root Directory ficar vazia, o `vercel.json` da raiz executa a instalação e o build dentro de `FRONTEND` e publica `FRONTEND/dist`.

Configure na Vercel:

```dotenv
VITE_API_URL=https://SEU-BACKEND.onrender.com/api/v1
```

Framework Preset deve ser **Vite** e o Output Directory deve ser `dist` quando `FRONTEND` estiver configurada como Root Directory. Depois de alterar essas opções ou a variável, execute um novo deploy de produção.

### Backend

No deploy Docker, a imagem executa as migrações automaticamente antes de iniciar
a API. Mantenha **Docker Command vazio** no Render e configure `SUPABASE_DB_URL`.
O histórico evita reaplicação nos reinícios. Isso prepara bancos novos, mas não
insere documentos: faça os uploads na Base de conhecimento. Bancos criados
manualmente precisam de revisão do histórico antes de usar esse fluxo.
Veja `BACKEND/database/supabase/README.md` para detalhes.

No serviço que executa o FastAPI, configure como segredos:

```dotenv
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=mistralai/mistral-large
OPENROUTER_EMBEDDING_MODEL=mistralai/mistral-embed-2312
EMBEDDING_DIMENSIONS=1024
SUPABASE_DB_URL=postgresql://postgres.PROJECT_REF:SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres
FRONTEND_ORIGIN=https://aurora-tech-chat.vercel.app
```

Nenhuma variável do Supabase deve ser criada na Vercel do frontend. O React conversa somente com a API FastAPI.

## Testes e qualidade

Backend:

```powershell
cd BACKEND
python -m pytest -q
python evaluation/evaluate_rag.py
```

A avaliação usa o endpoint real de embeddings e, portanto, consome créditos da chave configurada em `BACKEND/.env`.

Frontend:

```powershell
cd FRONTEND
npm test
npm run lint
npm run typecheck
npm run build
```

## Dados e segurança

- `.env`, ambientes virtuais, `node_modules` e builds são ignorados pelo Git;
- a chave OpenRouter e a URI PostgreSQL permanecem apenas no backend e nunca são enviadas ao React;
- o texto dos documentos e das perguntas é enviado ao OpenRouter para gerar embeddings; não envie material sensível sem revisar a política do provedor;
- logs registram método, rota, status e duração, sem corpos ou cabeçalhos;
- respostas Markdown são renderizadas com sanitização;
- documentos e embeddings ficam no Postgres do Supabase, protegidos por RLS e sem acesso para os papéis públicos.

Consulte [ESPECIFICACAO.md](./ESPECIFICACAO.md) para o escopo e [PLANO_IMPLEMENTACAO.md](./PLANO_IMPLEMENTACAO.md) para o histórico dos ciclos.

## Portal das entregas — roteiro para correção

A página inicial reúne as entregas **T1 a T5**. Cada página tem endereço próprio,
compatível com hospedagem estática e com os botões voltar/avançar do navegador:

| Página | Endereço após o domínio | Conteúdo |
| --- | --- | --- |
| Visão geral | `/#/entregas` | Percurso, contexto e acesso às cinco entregas |
| Trabalho 1 | `/#/entregas/1` | Modelos, rubrica, resultados históricos e decisão |
| Trabalho 2 | `/#/entregas/2` | Escopo, sete casos, métricas e falhas do baseline |
| Trabalho 3 | `/#/entregas/3` | Biblioteca, versões, testes registrados e pendências |
| Trabalho 4 | `/#/entregas/4` | Protótipo interativo, testes e mapa da entrega |
| Trabalho 5 | `/#/entregas/5` | Documentos, testes, rubrica e gate preliminar |
| Sobre | `/#/sobre` | Descrição do projeto, contexto acadêmico e integrantes do grupo |

T1–T3 funcionam sem backend e sintetizam os documentos em `entregas/`.
Os PDFs originais de T1/T2 e o DOCX de T3 estão disponíveis para download a partir
de cópias em `FRONTEND/public/entregas/`, incluídas no build da Vercel mesmo com
Root Directory = `FRONTEND`. Os testes conferem o SHA-256 dessas cópias.
Não há reexecução ou aprovação presumida dos experimentos históricos.

O conteúdo está em `FRONTEND/src/features/deliveries/`. Ao atualizar os relatórios,
revise o resumo em `utils/catalogue.ts`, a cópia pública e seu hash em
`services/sourceReports.ts`. Não publique credenciais ou documentos confidenciais.
Chat RAG e Base de conhecimento continuam acessíveis na navegação de laboratório.

## Trabalho 4 — fluxo textual integrado

A página **Trabalho 4 — Fluxo de Geração e Protótipo Textual**
está conectada ao fluxo real em `POST /api/v1/t4/run`; o chat RAG e os uploads
continuam disponíveis como recursos complementares. Consulte `TRABALHO_04_IMPLEMENTACAO.md`.

Inicie backend e frontend conforme as instruções acima e abra a aba **Trabalho 4**:

1. **Protótipo**: execute uma pergunta e inspecione etapas, prompt/versão, contexto, validação, latência, repetições e saídas brutas. A opção de corrigir solicita a pergunta completa; ela substitui a anterior.
2. **Testes e evidências**: carregue os 13 casos; E1/E2 são simulações explícitas sem chamada externa. Os outros casos usam OpenRouter. Revise os resultados e exporte CSV e JSON antes de recarregar a página.
3. Reaplique R1–R5 e L1–L2 do T2 e registre a avaliação humana. A tabela de comparação usa a primeira execução real de cada ID, sem substituir falhas por tentativas posteriores.
4. **Mapa da entrega**: confira requisitos, artefatos e pendências antes de montar o pacote.

O fluxo T4 usa `BACKEND/knowledge/politica_aurora_tech.txt`, não os documentos
carregados no Supabase. Suas chamadas dependem de `OPENROUTER_API_KEY`; o modo de
simulação não precisa dessa chave. No Docker, o início do serviço continua
dependendo da configuração do banco para as migrações do RAG.

Publique backend e frontend juntos. O Dockerfile inclui `prompts/` e `knowledge/`;
mantenha Docker Command vazio. Na Vercel, mantenha `VITE_API_URL` terminando em
`/api/v1` e faça novo build. `GET /api/v1/t4/config` permite conferir modelo,
parâmetros e versões sem expor segredos. O modelo efetivo deve ser
`mistralai/mistral-large`, preservando a escolha do T1 e o baseline T2.
Defina esse valor em `OPENROUTER_MODEL` no Render. O backend usa o valor do ambiente
sem sobrescrevê-lo. Reinicie/republique o backend para aplicar a configuração.
O frontend permite executar o modelo informado pela API.
Registros anteriores com outro modelo não são reescritos nem aceitos como
comparação equivalente com o baseline.

Os arquivos exportados ficam na máquina do avaliador: transfira os resultados para
`tests/resultados.csv`, salve o JSON em `evidencias/` e atualize a comparação em
`evaluation/comparacao_baseline.md`. Nenhum resultado é persistido no servidor ou
marcado como aprovado automaticamente. Não inclua dados pessoais nos testes.
A sessão do T4 é preservada ao navegar para outra entrega, mas não ao recarregar
ou fechar a página: exporte as evidências antes disso.

Para executar o protótipo textual do T4 após configurar `BACKEND/.env`:

```powershell
cd BACKEND
python run_t4.py
```

O fluxo carrega os templates por ID/versão, usa o TRH-04 para roteamento, verifica dados ausentes, monta o contexto mínimo da política, valida o contrato da saída e permite uma única repetição antes do fallback seguro.

### Diagnóstico de limites do OpenRouter

Veja [INTEGRACOES.md](INTEGRACOES.md) para a matriz de variáveis local/Render/Vercel e o diagnóstico seguro `python -m app.check_integrations --live`. O arquivo `env` da raiz não é carregado automaticamente: use `BACKEND/.env`. Variáveis do processo têm prioridade. O healthcheck não valida credenciais externas.

- HTTP 429 é identificado como `MODEL_RATE_LIMITED`, separado de HTTP 402 (`MODEL_CREDIT_LIMIT`). Ter saldo não impede limites de requisições/capacidade.
- O T4 respeita `Retry-After` em segundos ou data HTTP. Sem um cabeçalho válido, espera 2 segundos. Faz no máximo **uma repetição no fluxo inteiro**, compartilhada com falhas de formato/técnicas; não há retries ocultos no cliente HTTP.
- A espera automática é de no máximo 30 segundos. Se o serviço pedir mais, o fluxo encerra com fallback e informa o intervalo, sem antecipar a repetição. HTTP 402 e erros de autenticação não são repetidos automaticamente.
- A repetição de HTTP 429 usa os mesmos prompts e `mistralai/mistral-large`; não troca de modelo nem acrescenta instruções de correção de formato.
- A tela, as evidências JSON/CSV e o log `aurora.openrouter` registram HTTP, origem reconhecida, categoria normalizada e espera informada. O rastro e as evidências também mostram a espera aplicada antes da repetição. O retorno bruto do provedor, mensagens livres, nomes de provedores e credenciais não são copiados para logs ou diagnósticos públicos. Sem metadados reconhecidos, a origem permanece desconhecida; não se presume falta de saldo.
- A repetição automática de 429 é específica do fluxo T4. O chat RAG recebe o diagnóstico seguro, mas não ganha chamadas automáticas adicionais.

Referência: [limites da API de inferência do OpenRouter](https://openrouter.ai/docs/api_reference/limits). Os limites da Data API de rankings não se aplicam a este endpoint de chat.

Os 13 casos exigidos estão em `tests/casos.csv`; os resultados reais devem ser registrados em `tests/resultados.csv`. O diagrama está em `architecture/fluxo.png` e a comparação com o baseline em `evaluation/comparacao_baseline.md`.
# Trabalho 6 — entrega final

A rota `#/entregas/6` consolida o projeto com versão identificada, arquitetura, vinte casos, seis cenas de demonstração, rubrica humana, riscos, gate e exportação ZIP/PDF/JSON. Os rascunhos ficam no navegador; exporte o JSON para preservar as evidências.

Antes de publicar mudanças, execute a partir de `BACKEND`: `.venv/Scripts/python evaluation/freeze_final.py`. Isso atualiza o manifesto compartilhado pelo frontend/backend, as entradas sintéticas e o arquivo de código permitido em `BACKEND/release`. Publique ambos os serviços com esses artefatos. Qualquer alteração de código, configuração, prompts, base ou testes exige novo congelamento e reexecução dos vinte casos. O comando usa a configuração pública do ambiente atual, sem exportar credenciais.

As notas, contribuições, ensaio e decisão precisam ser preenchidos pelo grupo. O sistema não atribui notas humanas nem transforma testes automatizados em resultados acadêmicos. Custos podem ser registrados como valores observados com referência às chamadas do provedor; a média requer todos os casos reais. O pacote é explicitamente um rascunho até a decisão sustentada por evidências. Guia: `FRONTEND/public/entregas/t6/guia.md`.
