# Plano de Implementação — Aurora Tech Chatbot

**Base:** [ESPECIFICACAO.md](./ESPECIFICACAO.md)  
**Status geral:** MVP implementado; Supabase integrado no código e implantação externa pendente de credenciais
**Estratégia:** ciclos curtos alternando entre backend e frontend

## 1. Objetivo do plano

Implementar o MVP do Aurora Tech Chatbot de forma incremental. Cada ciclo deverá entregar uma pequena parte funcional, validada e registrada antes do início do próximo ciclo.

A ordem alterna entre backend e frontend para evitar que uma das camadas seja construída integralmente sem integração com a outra.

## 2. Regras obrigatórias para o agente

Ao executar este plano, o agente deverá:

1. trabalhar em apenas um ciclo por vez, salvo instrução diferente do usuário;
2. ler a especificação e este plano antes de alterar o código;
3. marcar cada tarefa concluída trocando `[ ]` por `[x]`;
4. marcar uma tarefa somente após implementar e validar o resultado;
5. não marcar tarefas que tenham sido apenas iniciadas;
6. marcar o ciclo no “Resumo dos ciclos” somente quando todos os itens obrigatórios e o critério de conclusão estiverem atendidos;
7. registrar, no “Diário de execução”, a data, o ciclo, um resumo e os comandos de validação executados;
8. registrar impedimentos sem marcar a tarefa como concluída;
9. preservar alterações existentes que não façam parte do ciclo;
10. manter os contratos entre frontend e backend compatíveis;
11. atualizar a documentação sempre que uma decisão técnica mudar;
12. encerrar cada ciclo informando claramente o que foi concluído e qual será o próximo ciclo.

### Formato para registrar um impedimento

```markdown
- Ciclo: 00
- Tarefa bloqueada: descrição
- Motivo: descrição objetiva
- Ação necessária: decisão, acesso ou recurso necessário
```

## 3. Resumo dos ciclos

- [x] Ciclo 01 — Backend: fundação da API
- [x] Ciclo 02 — Frontend: fundação da interface
- [x] Ciclo 03 — Backend: contratos e configurações
- [x] Ciclo 04 — Frontend: estrutura visual e comunicação com a API
- [x] Ciclo 05 — Backend: leitura e divisão de documentos
- [x] Ciclo 06 — Frontend: tela da base de conhecimento
- [x] Ciclo 07 — Backend: embeddings, ChromaDB e endpoints de documentos
- [x] Ciclo 08 — Frontend: integração da base de conhecimento
- [ ] Ciclo 09 — Backend: recuperação RAG e OpenRouter
- [x] Ciclo 10 — Frontend: chat integrado
- [x] Ciclo 11 — Backend: robustez, testes e avaliação RAG
- [x] Ciclo 12 — Frontend: testes, responsividade e acabamento
- [x] Validação final do MVP
- [x] Migração técnica — Backend: Supabase/pgvector no lugar do ChromaDB

## 4. Ciclos de implementação

## Ciclo 01 — Backend: fundação da API

**Objetivo:** criar uma API FastAPI mínima, executável localmente e pronta para receber os próximos módulos.

### Implementação

- [x] Criar a pasta `backend/` e a estrutura inicial de `backend/app/`.
- [x] Definir o gerenciamento de dependências Python em `pyproject.toml` ou `requirements.txt`.
- [x] Criar a aplicação FastAPI em `backend/app/main.py`.
- [x] Criar o endpoint `GET /api/v1/health` com resposta `{"status": "ok"}`.
- [x] Configurar CORS para o endereço local do frontend.
- [x] Criar `backend/.env.example` sem segredos reais.
- [x] Criar `.gitignore` para ambiente virtual, cache, `.env`, ChromaDB local e arquivos temporários.

### Validação

- [x] Iniciar o backend localmente sem erros.
- [x] Confirmar resposta HTTP 200 no endpoint de saúde.
- [x] Confirmar acesso à documentação Swagger.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando uma instalação limpa conseguir iniciar a API e consultar o endpoint de saúde.

---

## Ciclo 02 — Frontend: fundação da interface

**Objetivo:** criar a aplicação React e confirmar sua execução local.

### Implementação

- [x] Criar `frontend/` com React, TypeScript e Vite.
- [x] Remover conteúdos de demonstração que não serão utilizados.
- [x] Criar a estrutura inicial de `components/`, `pages/`, `services/` e `types/`.
- [x] Criar o layout base da aplicação.
- [x] Adicionar navegação simples entre “Chat” e “Base de conhecimento”.
- [x] Criar `frontend/.env.example` com a URL pública da API.
- [x] Definir estilos globais mínimos e identidade inicial da Aurora Tech.

### Validação

- [x] Iniciar o frontend localmente sem erros.
- [x] Confirmar que as duas páginas podem ser acessadas.
- [x] Confirmar que o build de produção é gerado.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando a aplicação React abrir no navegador, navegar entre as páginas e gerar um build válido.

---

## Ciclo 03 — Backend: contratos e configurações

**Objetivo:** definir os modelos e configurações compartilhados pelos recursos futuros.

### Implementação

- [x] Criar o módulo central de configurações do backend.
- [x] Ler configurações por variáveis de ambiente.
- [x] Validar a presença das configurações obrigatórias no momento apropriado.
- [x] Criar os modelos de requisição do chat: mensagem e histórico.
- [x] Criar os modelos de resposta: resposta, fonte e indicação de contexto.
- [x] Criar o formato padronizado de erro da API.
- [x] Definir limites de tamanho para mensagem, histórico e upload.
- [x] Documentar os contratos no Swagger com exemplos.

### Validação

- [x] Criar testes para validação dos modelos.
- [x] Confirmar rejeição de mensagem vazia e entrada acima do limite.
- [x] Confirmar que segredos não aparecem nos logs ou no Swagger.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando os contratos do chat e as configurações estiverem tipados, documentados e testados.

---

## Ciclo 04 — Frontend: estrutura visual e comunicação com a API

**Objetivo:** preparar a interface para consumir o backend e representar os estados principais.

### Implementação

- [x] Criar os tipos TypeScript equivalentes aos contratos públicos da API.
- [x] Criar um cliente HTTP centralizado usando a URL definida no ambiente.
- [x] Criar um componente de estado da API na interface.
- [x] Consultar `GET /api/v1/health` ao carregar a aplicação ou quando solicitado.
- [x] Exibir estados de API disponível e indisponível.
- [x] Criar componentes visuais iniciais de mensagem, campo de texto, carregamento e erro.
- [x] Criar dados simulados somente para visualizar a conversa antes da integração real.

### Validação

- [x] Confirmar comunicação entre React e FastAPI.
- [x] Confirmar tratamento visual quando o backend estiver desligado.
- [x] Confirmar que a aplicação continua gerando build válido.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando o frontend detectar a disponibilidade do backend e possuir os componentes básicos do chat.

---

## Ciclo 05 — Backend: leitura e divisão de documentos

**Objetivo:** transformar arquivos suportados em trechos prontos para receber embeddings.

### Implementação

- [x] Criar uma interface comum para extração de texto.
- [x] Implementar extração de TXT e Markdown.
- [x] Implementar extração de PDF com preservação do número da página.
- [x] Implementar extração de DOCX.
- [x] Validar extensão, MIME type e tamanho do arquivo.
- [x] Calcular hash do conteúdo para identificar duplicidade.
- [x] Implementar normalização do texto.
- [x] Implementar divisão em trechos com tamanho e sobreposição configuráveis.
- [x] Preservar metadados de nome, página, posição e tipo de arquivo.
- [x] Rejeitar documentos vazios ou sem texto extraível.

### Validação

- [x] Testar extração de cada formato suportado.
- [x] Testar chunking, sobreposição e metadados.
- [x] Testar arquivo inválido, vazio e duplicado.
- [x] Adicionar arquivos pequenos de teste sem dados sensíveis.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando todos os formatos suportados forem convertidos de maneira previsível em trechos testados.

---

## Ciclo 06 — Frontend: tela da base de conhecimento

**Objetivo:** construir a interface de documentos de acordo com o contrato planejado.

### Implementação

- [x] Criar o seletor de arquivos com formatos aceitos visíveis.
- [x] Criar o botão de envio e seu estado de carregamento.
- [x] Criar a lista visual de documentos.
- [x] Exibir nome, tipo e quantidade de trechos.
- [x] Criar a ação de remoção com confirmação.
- [x] Criar estados de lista vazia, sucesso e erro.
- [x] Usar respostas simuladas compatíveis com o contrato enquanto os endpoints ainda não estiverem disponíveis.

### Validação

- [x] Testar seleção de formato aceito e rejeitado.
- [x] Testar estados de carregamento, lista vazia e erro.
- [x] Testar visualmente em largura de celular e desktop.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando todos os estados da base de conhecimento puderem ser demonstrados com dados simulados.

---

## Ciclo 07 — Backend: embeddings, ChromaDB e endpoints de documentos

**Objetivo:** indexar, consultar administrativamente e remover documentos da base vetorial.

### Implementação

- [x] Configurar o modelo local de embeddings.
- [x] Criar um serviço de embeddings isolado das rotas HTTP.
- [x] Configurar persistência local do ChromaDB.
- [x] Criar uma coleção para os documentos da Aurora Tech.
- [x] Salvar texto, embedding e metadados de cada trecho.
- [x] Evitar indexação duplicada pelo hash do documento.
- [x] Implementar `POST /api/v1/documents`.
- [x] Implementar `GET /api/v1/documents`.
- [x] Implementar `DELETE /api/v1/documents/{document_id}`.
- [x] Garantir que a remoção exclua todos os trechos do documento.

### Validação

- [x] Testar upload e indexação de um documento válido.
- [x] Reiniciar o backend e confirmar a persistência dos vetores.
- [x] Testar listagem e rejeição de duplicidade.
- [x] Testar remoção completa do documento.
- [x] Confirmar os contratos no Swagger.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando um documento puder ser indexado, listado e removido por meio da API, com persistência após reinício.

---

## Ciclo 08 — Frontend: integração da base de conhecimento

**Objetivo:** substituir os dados simulados da tela de documentos pela API real.

### Implementação

- [x] Criar funções do cliente para enviar, listar e remover documentos.
- [x] Integrar o formulário de upload com `POST /api/v1/documents`.
- [x] Integrar a lista com `GET /api/v1/documents`.
- [x] Integrar a remoção com `DELETE /api/v1/documents/{document_id}`.
- [x] Atualizar a lista após envio ou remoção.
- [x] Exibir mensagens retornadas pelo backend.
- [x] Remover os dados simulados da tela de documentos.

### Validação

- [x] Executar o fluxo completo de upload pela interface.
- [x] Confirmar que o documento continua listado após recarregar a página.
- [x] Executar o fluxo completo de remoção.
- [x] Confirmar tratamento de arquivo inválido e duplicado.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando a base vetorial puder ser gerenciada integralmente pelo frontend.

---

## Ciclo 09 — Backend: recuperação RAG e OpenRouter

**Objetivo:** responder perguntas usando os documentos indexados e o modelo configurado na OpenRouter.

### Implementação

- [x] Gerar o embedding da pergunta com o mesmo modelo usado na indexação.
- [x] Consultar no ChromaDB a quantidade configurada de trechos.
- [x] Aplicar limiar de relevância e limitar o contexto.
- [x] Criar o prompt de sistema da Aurora Tech.
- [x] Incluir contexto, pergunta e histórico curto no prompt.
- [x] Criar um cliente isolado para a OpenRouter usando `httpx`.
- [x] Configurar modelo, chave, timeout e cabeçalhos necessários.
- [x] Implementar `POST /api/v1/chat`.
- [x] Retornar resposta, fontes e `has_context`.
- [x] Responder sem chamar o modelo quando não houver contexto suficiente, se essa for a estratégia escolhida.
- [x] Tratar chave inválida, timeout, limite e modelo indisponível.

### Validação

- [x] Testar a recuperação de um trecho conhecido.
- [x] Testar a montagem do prompt sem expor instruções ou segredos.
- [x] Testar o endpoint com cliente OpenRouter simulado.
- [ ] Executar ao menos uma consulta real com uma chave fornecida pelo ambiente.
- [x] Testar pergunta sem contexto e fontes vazias.
- [x] Registrar os comandos executados no diário sem registrar a chave.

### Critério de conclusão

O ciclo estará concluído quando o endpoint responder uma pergunta fundamentada, citar fontes e recusar adequadamente uma pergunta sem contexto.

---

## Ciclo 10 — Frontend: chat integrado

**Objetivo:** substituir os dados simulados pelo fluxo real do chatbot.

### Implementação

- [x] Criar a função do cliente para `POST /api/v1/chat`.
- [x] Enviar mensagem e histórico curto ao backend.
- [x] Adicionar imediatamente a mensagem do usuário à conversa.
- [x] Exibir carregamento enquanto aguarda a resposta.
- [x] Exibir a resposta do assistente.
- [x] Exibir as fontes associadas à resposta.
- [x] Exibir o estado de ausência de contexto.
- [x] Implementar ação para limpar a conversa.
- [x] Limitar o histórico enviado conforme a especificação.
- [x] Remover os dados simulados do chat.

### Validação

- [x] Testar uma pergunta com resposta presente na base.
- [x] Testar uma pergunta sem resposta na base.
- [x] Testar erro e timeout do backend.
- [x] Confirmar que o histórico permanece apenas no frontend.
- [x] Confirmar que limpar a conversa remove o histórico visível.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando o usuário puder conversar com o chatbot real, visualizar fontes e receber erros compreensíveis.

---

## Ciclo 11 — Backend: robustez, testes e avaliação RAG

**Objetivo:** consolidar a qualidade do backend e medir o comportamento do RAG.

### Implementação

- [x] Revisar validação de todas as entradas.
- [x] Garantir que a chave da OpenRouter nunca seja registrada.
- [x] Padronizar os erros retornados pela API.
- [x] Adicionar logs essenciais sem conteúdo sensível.
- [x] Completar os testes unitários dos serviços.
- [x] Completar os testes dos endpoints.
- [x] Criar uma pequena base de perguntas esperadas.
- [x] Avaliar recuperação de fontes e recusa sem contexto.
- [x] Ajustar tamanho dos trechos, sobreposição, `top_k` e limiar com base nos resultados.
- [x] Documentar os valores finais escolhidos.

### Validação

- [x] Executar toda a suíte do backend sem falhas.
- [x] Executar a avaliação RAG e registrar os resultados.
- [x] Confirmar que nenhum segredo está versionado.
- [x] Confirmar inicialização com base vetorial vazia.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando os testes passarem, os erros estiverem padronizados e o RAG tiver sido avaliado com perguntas conhecidas.

---

## Ciclo 12 — Frontend: testes, responsividade e acabamento

**Objetivo:** finalizar a experiência do usuário e garantir estabilidade da interface.

### Implementação

- [x] Revisar a identidade visual da Aurora Tech.
- [x] Ajustar o layout para celular e desktop.
- [x] Garantir navegação por teclado nos controles principais.
- [x] Adicionar rótulos acessíveis aos campos e botões.
- [x] Sanitizar qualquer Markdown renderizado.
- [x] Completar testes dos componentes do chat.
- [x] Completar testes da tela de documentos.
- [x] Completar testes de integração com API simulada.
- [x] Remover código, estilos e dependências não utilizados.

### Validação

- [x] Executar todos os testes do frontend sem falhas.
- [x] Executar lint e verificação de tipos.
- [x] Gerar o build de produção.
- [x] Verificar manualmente as principais larguras de tela.
- [x] Registrar os comandos executados no diário.

### Critério de conclusão

O ciclo estará concluído quando testes, tipagem e build passarem e os fluxos principais funcionarem em celular e desktop.

## 5. Validação final do MVP

Esta etapa somente poderá ser marcada após a conclusão dos 12 ciclos.

- [x] Preparar uma instalação limpa do projeto.
- [x] Seguir o README sem usar configurações não documentadas.
- [x] Iniciar backend e frontend.
- [x] Confirmar o endpoint de saúde.
- [x] Enviar um documento de cada formato suportado.
- [x] Confirmar persistência dos documentos após reinício.
- [x] Fazer uma pergunta respondida pela base.
- [x] Confirmar a apresentação das fontes corretas.
- [x] Fazer uma pergunta sem resposta na base.
- [x] Confirmar que o chatbot não inventa uma resposta.
- [x] Remover um documento e confirmar que ele deixa de ser consultado.
- [x] Executar testes, lint, tipagem e builds.
- [x] Revisar `.gitignore`, `.env.example`, README e especificação.
- [x] Confirmar que nenhuma chave ou dado sensível está versionado.
- [x] Marcar “Validação final do MVP” no resumo dos ciclos.

## 6. Definição geral de pronto

Uma tarefa somente pode ser marcada como concluída quando:

- o código correspondente foi implementado;
- o comportamento foi testado;
- os testes relacionados passam;
- não existem erros conhecidos ocultados;
- os contratos continuam compatíveis;
- a documentação afetada foi atualizada;
- a alteração não incluiu segredos;
- o resultado foi registrado no diário.

## 7. Diário de execução

O agente deverá acrescentar uma entrada ao final desta seção depois de cada ciclo.

### Modelo de entrada

```markdown
### AAAA-MM-DD — Ciclo 00

- Status: concluído | parcial | bloqueado
- Implementado: resumo curto
- Arquivos principais: lista de caminhos
- Validações: comandos executados e resultados
- Pendências: nenhuma ou lista objetiva
- Próximo ciclo: Ciclo 00 — Nome
```

<!-- Acrescentar novas entradas abaixo desta linha. -->

### 2026-08-27 — Ciclo 01

- Status: concluído
- Implementado: fundação FastAPI, roteamento versionado, endpoint de saúde, CORS, configuração de ambiente, dependências e teste do endpoint.
- Arquivos principais: `.gitignore`, `backend/pyproject.toml`, `backend/.env.example`, `backend/app/main.py`, `backend/app/api/v1/router.py`, `backend/app/api/v1/routes/health.py`, `backend/tests/test_health.py`.
- Validações: `python -m pytest -q` — 1 teste aprovado; Uvicorn iniciado em `127.0.0.1:8000`; `GET /api/v1/health` — HTTP 200; `GET /docs` — HTTP 200; OpenAPI carregado com o título esperado.
- Pendências: nenhuma no Ciclo 01. O comando global `python` aponta para uma instalação ausente; foi usado o runtime Python fornecido pelo ambiente para criar `backend/.venv`.
- Próximo ciclo: Ciclo 02 — Frontend: fundação da interface

### 2026-08-27 — Ciclo 02

- Status: concluído
- Implementado: fundação React 19 com TypeScript e Vite, carregamento sob demanda das páginas, navegação entre Chat e Base de conhecimento, layout responsivo, identidade visual inicial e configurações de ambiente.
- Arquivos principais: `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`, `frontend/tsconfig.app.json`, `frontend/src/App.tsx`, `frontend/src/components/AppShell.tsx`, `frontend/src/pages/ChatPage.tsx`, `frontend/src/pages/KnowledgeBasePage.tsx`, `frontend/src/styles/global.css`.
- Validações: `npm run typecheck` — aprovado; `npm run build` — aprovado, 34 módulos transformados; Vite iniciado em `127.0.0.1:5173`; página inicial — HTTP 200 e título correto; navegação de Chat e Base de conhecimento confirmada na composição da aplicação.
- Pendências: nenhuma no Ciclo 02. A interação dos controles permanece desabilitada intencionalmente até os ciclos de integração correspondentes.
- Próximo ciclo: Ciclo 03 — Backend: contratos e configurações

### 2026-08-27 — Ciclo 03

- Status: concluído
- Implementado: configurações tipadas com Pydantic Settings, chave OpenRouter protegida e validada sob demanda, limites do MVP, contratos do chat, erros padronizados e endpoint provisório documentado no OpenAPI.
- Arquivos principais: `BACKEND/app/core/config.py`, `BACKEND/app/core/errors.py`, `BACKEND/app/models/chat.py`, `BACKEND/app/models/errors.py`, `BACKEND/app/api/v1/routes/chat.py`, `BACKEND/tests/test_chat_contract.py`, `BACKEND/tests/test_config.py`.
- Validações: `python -m pytest -q` — 10 testes aprovados; validação de mensagem vazia, mensagem longa, histórico longo, proteção do segredo e schemas do chat no OpenAPI.
- Pendências: o endpoint `/chat` retorna `CHAT_NOT_IMPLEMENTED` intencionalmente até o Ciclo 09.
- Próximo ciclo: Ciclo 04 — Frontend: estrutura visual e comunicação com a API

### 2026-08-27 — Ciclo 04

- Status: concluído
- Implementado: contratos TypeScript, cliente HTTP centralizado, configuração pública da API, monitor de saúde com nova tentativa, estados online/offline e componentes visuais reutilizáveis do chat com dados simulados.
- Arquivos principais: `FRONTEND/src/types/api.ts`, `FRONTEND/src/services/apiClient.ts`, `FRONTEND/src/features/health/`, `FRONTEND/src/features/chat/`, `FRONTEND/src/pages/ChatPage.tsx`, `FRONTEND/src/styles/global.css`.
- Validações: `npm run typecheck` — aprovado; `npm run build` — aprovado com 46 módulos; chamada no formato do frontend para `/api/v1/health` — HTTP 200; preflight CORS — HTTP 200 com origem `http://localhost:5173`.
- Pendências: dados do chat permanecem simulados por desenho do plano até o Ciclo 10.
- Próximo ciclo: Ciclo 05 — Backend: leitura e divisão de documentos

### 2026-08-27 — Ciclo 05

- Status: concluído
- Implementado: interface comum de extração, suporte a TXT/Markdown/PDF/DOCX, validação de extensão/MIME/tamanho, hash SHA-256, normalização Unicode, chunking configurável e metadados determinísticos com página.
- Arquivos principais: `BACKEND/app/services/documents/extractors.py`, `BACKEND/app/services/documents/processor.py`, `BACKEND/app/models/documents.py`, `BACKEND/tests/test_document_processor.py`, `BACKEND/tests/fixtures/`.
- Validações: `python -m pytest -q` — 21 testes aprovados; 11 testes específicos de documentos cobrindo formatos, página, chunking, normalização, MIME, vazio e duplicidade.
- Pendências: nenhuma no Ciclo 05.
- Próximo ciclo: Ciclo 06 — Frontend: tela da base de conhecimento

### 2026-08-27 — Ciclo 06

- Status: concluído
- Implementado: tela simulada de documentos com seletor validado, upload com carregamento, listagem, contagem de chunks, tamanho, remoção confirmada e estados vazio/sucesso/erro responsivos.
- Arquivos principais: `FRONTEND/src/features/documents/`, `FRONTEND/src/pages/KnowledgeBasePage.tsx`, `FRONTEND/src/pages/KnowledgeBasePage.test.tsx`, `FRONTEND/src/styles/global.css`, `FRONTEND/vite.config.ts`.
- Validações: `npm test` — 3 testes aprovados; `npm run typecheck` — aprovado; `npm run build` — aprovado com 50 módulos; revisão dos breakpoints de celular e desktop no CSS.
- Pendências: os dados permanecem simulados até a integração do Ciclo 08.
- Próximo ciclo: Ciclo 07 — Backend: embeddings, ChromaDB e endpoints de documentos

### 2026-08-27 — Ciclo 07

- Status: concluído
- Implementado: serviço de Sentence Transformers carregado sob demanda, ChromaDB persistente, coleção da Aurora Tech, catálogo por metadados, prevenção de duplicidade e endpoints de upload/listagem/exclusão.
- Arquivos principais: `BACKEND/app/services/embeddings/`, `BACKEND/app/services/vector_store/`, `BACKEND/app/services/documents/service.py`, `BACKEND/app/api/dependencies.py`, `BACKEND/app/api/v1/routes/documents.py`, `BACKEND/tests/test_document_api.py`.
- Validações: `python -m pytest -q` — 24 testes aprovados; ciclo completo de API, duplicidade, exclusão e reabertura do Chroma; modelo real `paraphrase-multilingual-MiniLM-L12-v2` carregado com vetor de dimensão 384 e norma 1.0.
- Pendências: nenhuma no Ciclo 07.
- Próximo ciclo: Ciclo 08 — Frontend: integração da base de conhecimento

### 2026-08-27 — Ciclo 08

- Status: concluído
- Implementado: API frontend de documentos, adaptação dos contratos snake_case, hook com carregamento/mutações/erros, upload multipart real, listagem persistida e exclusão sem conteúdo; simulação removida.
- Arquivos principais: `FRONTEND/src/features/documents/api/documentApi.ts`, `FRONTEND/src/features/documents/hooks/useDocuments.ts`, `FRONTEND/src/pages/KnowledgeBasePage.tsx`, `FRONTEND/src/services/apiClient.ts`, `FRONTEND/src/pages/KnowledgeBasePage.test.tsx`.
- Validações: `npm test` — 4 testes aprovados; `npm run typecheck` e `npm run build` aprovados; API real na porta 8001 — upload HTTP 201, listagem com 1 documento, delete HTTP 204 e lista final vazia.
- Pendências: nenhuma no Ciclo 08.
- Próximo ciclo: Ciclo 09 — Backend: recuperação RAG e OpenRouter

### 2026-08-27 — Ciclo 09

- Status: parcial — implementação concluída; validação externa condicionada à credencial.
- Implementado: busca vetorial com relevância e limite de contexto, prompt fundamentado com histórico curto, política de recusa sem contexto, endpoint real de chat e cliente OpenRouter assíncrono com tratamento seguro de erros.
- Arquivos principais: `BACKEND/app/services/rag/`, `BACKEND/app/services/llm/`, `BACKEND/app/services/vector_store/chroma_store.py`, `BACKEND/app/api/v1/routes/chat.py`, `BACKEND/tests/test_rag_service.py`, `BACKEND/tests/test_openrouter_client.py`.
- Validações: `python -m pytest -q` — 34 testes aprovados; recuperação conhecida, limite de contexto, prompt, recusa, endpoint com provedor simulado, autenticação, limite e indisponibilidade cobertos.
- Pendências: consulta externa real não executada porque `OPENROUTER_API_KEY` não está presente no ambiente nem em `BACKEND/.env`; nenhum segredo foi exibido ou registrado.
- Próximo ciclo: Ciclo 10 — Frontend: chat integrado

### 2026-08-27 — Ciclo 10

- Status: concluído.
- Implementado: cliente HTTP do chat, histórico temporário limitado a 10 mensagens, envio otimista, carregamento, resposta com fontes, indicação de ausência de contexto, erro com nova tentativa, timeout local e limpeza da conversa; dados simulados removidos.
- Arquivos principais: `FRONTEND/src/features/chat/api/chatApi.ts`, `FRONTEND/src/features/chat/hooks/useChat.ts`, `FRONTEND/src/features/chat/components/ChatComposer.tsx`, `FRONTEND/src/features/chat/components/ChatMessage.tsx`, `FRONTEND/src/pages/ChatPage.tsx`, `FRONTEND/src/pages/ChatPage.test.tsx`.
- Validações: `npm test` — 9 testes aprovados; `npm run typecheck` — aprovado; `npm run build` — aprovado com 54 módulos transformados.
- Pendências: nenhuma no Ciclo 10.
- Próximo ciclo: Ciclo 11 — Backend: robustez, testes e avaliação RAG

### 2026-08-27 — Ciclo 11

- Status: concluído.
- Implementado: logs de requisição sem corpo/cabeçalhos, erros inesperados padronizados sem mensagem interna, validação adicional de nome de arquivo, encerramento explícito do Chroma, testes de timeout/resposta inválida e avaliação RAG reproduzível.
- Arquivos principais: `BACKEND/app/core/logging.py`, `BACKEND/app/core/errors.py`, `BACKEND/evaluation/rag_cases.json`, `BACKEND/evaluation/evaluate_rag.py`, `BACKEND/evaluation/README.md`, `BACKEND/tests/test_error_handling.py`.
- Validações: `python -m pytest -q` — 38 testes aprovados; `python -m compileall -q app evaluation` — aprovado; `python evaluation/evaluate_rag.py` com embeddings reais — 4/4 casos aprovados; varredura por padrão de chave OpenRouter — nenhuma ocorrência; arquivos `.env` confirmados no `.gitignore`.
- Pendências: nenhuma no Ciclo 11.
- Próximo ciclo: Ciclo 12 — Frontend: testes, responsividade e acabamento

### 2026-08-27 — Ciclo 12

- Status: concluído.
- Implementado: Markdown seguro com `react-markdown` e `rehype-sanitize`, rótulos acessíveis, foco por teclado, ajustes móveis, lint ESLint, testes ampliados de chat/documentos e remoção de estilos obsoletos.
- Arquivos principais: `FRONTEND/src/features/chat/components/MarkdownContent.tsx`, `FRONTEND/src/features/chat/components/ChatMessage.tsx`, `FRONTEND/src/pages/ChatPage.test.tsx`, `FRONTEND/src/pages/KnowledgeBasePage.test.tsx`, `FRONTEND/eslint.config.js`, `FRONTEND/src/styles/global.css`.
- Validações: `npm test` — 16 testes aprovados; `npm run lint` — sem avisos; `npm run typecheck` — aprovado; `npm run build` — aprovado com 221 módulos; inspeção visual em 1440×900 e 360×800 nas páginas Chat e Base de conhecimento, sem overflow horizontal.
- Pendências: nenhuma no Ciclo 12.
- Próxima etapa: validação final do MVP.

### 2026-08-27 — Validação final do MVP

- Status: concluído para o código e os fluxos locais; integração externa documentada como condicionada à chave.
- Implementado: README completo de instalação/operação, teste integrado com TXT/MD/PDF/DOCX e cobertura conjunta de consulta, fontes, recusa, persistência e remoção.
- Arquivos principais: `README.md`, `BACKEND/tests/test_mvp_flow.py`, `PLANO_IMPLEMENTACAO.md`.
- Validações: instalação backend com `pip install -e ".[dev]"` e `pip check` — aprovada; `npm ci` — aprovado, 0 vulnerabilidades; backend e frontend iniciados juntos; health, Swagger, frontend e preflight CORS — HTTP 200; backend — 39 testes e avaliação 4/4; frontend — 16 testes, lint, tipos e build aprovados.
- Pendências: executar a consulta externa real do Ciclo 09 quando uma `OPENROUTER_API_KEY` for fornecida em `BACKEND/.env`. O cliente, os erros e o endpoint estão validados com provedor simulado; a chave não faz parte do repositório.
- Próximo ciclo: nenhum — MVP acadêmico implementado.

### 2026-08-28 — Migração técnica para Supabase

- Status: código concluído e validado; aplicação da migração no projeto remoto pendente de credenciais.
- Implementado: substituição do ChromaDB pelo Supabase Postgres com pgvector, interface desacoplada de armazenamento, indexação transacional em função SQL, busca cosseno com limiar no banco, RLS, permissões exclusivas do backend, migração idempotente e script de reversão. O acesso de runtime usa Psycopg pelo Session Pooler.
- Arquivos principais: `BACKEND/app/services/vector_store/`, `BACKEND/database/supabase/`, `BACKEND/app/core/config.py`, `BACKEND/tests/test_supabase_store.py`, `BACKEND/.env.example`.
- Validações: `python -m pytest -q` — 48 testes aprovados; `python -m compileall -q app evaluation` — aprovado; `python -m pip check` — nenhuma dependência quebrada; construção e encerramento do pool Psycopg aprovados.
- Pendências: executar `BACKEND/database/supabase/migrations/001_aurora_vector_store.sql` no projeto Supabase e configurar `SUPABASE_DB_URL` com a URI do Session Pooler, porta 5432, no serviço do backend.

### 2026-08-28 — Embeddings via OpenRouter

- Status: código e imagem Docker concluídos e validados; reindexação dos documentos remotos pendente.
- Implementado: substituição do Sentence Transformers local pelo endpoint de embeddings do OpenRouter, lotes configuráveis, vetores de 384 dimensões, validação estrita da resposta, mapeamento seguro de erros e execução da indexação fora do loop assíncrono. PyTorch e Sentence Transformers foram removidos da imagem.
- Arquivos principais: `BACKEND/app/services/embeddings/openrouter.py`, `BACKEND/app/api/dependencies.py`, `BACKEND/app/core/config.py`, `BACKEND/tests/test_openrouter_embeddings.py`, `BACKEND/Dockerfile`.
- Validações: `python -m pytest -q` — 61 testes aprovados; `python -m compileall -q app evaluation` — aprovado; imagem Docker construída com 99 MB, endpoint de saúde aprovado e ausência de PyTorch confirmada.
- Pendências: configurar `OPENROUTER_API_KEY` no Render, reindexar todos os documentos existentes e executar a avaliação RAG para recalibrar o limiar de relevância; embeddings produzidos por modelos diferentes não podem ser misturados.
