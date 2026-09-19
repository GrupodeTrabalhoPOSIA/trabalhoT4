# Trabalho 4 — Fluxo de Geração e Protótipo Textual

## O que foi incorporado

O repositório existente foi preservado. O T4 foi acrescentado como uma camada de orquestração em `BACKEND/app/services/t4/`, sem remover o chatbot RAG anterior.

O fluxo implementado segue: entrada → validação → TRH-04 → verificação de dados → carregamento do template/versionamento → contexto mínimo → modelo → validação → resposta, pergunta, recusa/encaminhamento ou fallback.

O modelo de geração é `mistralai/mistral-large`, escolhido no T1 e mantido no T2,
T3, T4 e chat RAG. O backend normaliza configurações antigas/divergentes com aviso
no log, sem substituir o modelo por outra família em caso de falha. O frontend
exibe tanto o modelo esperado quanto o informado pela API e bloqueia novas
execuções reais do T4 se a API antiga divergir. Mistral Embed continua exclusivo
da recuperação de documentos; não é o modelo de geração.

## Análise do atendimento e integração web

A versão anterior expunha somente o chat RAG em `/api/v1/chat`, enquanto o fluxo
T4 era executado por `run_t4.py`. Portanto, a interface web anterior não evidenciava
o roteamento TRH-04, os contratos dos especialistas nem o registro dos testes.

A página inicial agora é o protótipo do Trabalho 4 e consome `/api/v1/t4/run`.
`/api/v1/t4/config` informa modelo, parâmetros, base e versões. A organização
React separa tela, componentes, estado e serviços na feature `t4`.

| Requisito do enunciado | Implementação / evidência | Limite |
|---|---|---|
| Fluxo executável e exceções | Rastro do backend exibido por etapa; diagrama em `architecture/fluxo.png` e fonte atualizada em `architecture/fluxo.mmd` | Rastro exibido ao término, sem streaming |
| Carregamento por ID/versão | `PromptRegistry`; arquivos incluídos no Docker | Originais T3 ainda precisam de conferência |
| Ambiguidade e dado ausente | Confiança inferior a 70% e contexto ambíguo de elegibilidade pedem esclarecimento; função ausente impede especialista | Detecção de função é heurística e precisa ser avaliada com casos reais |
| Correção e contexto mínimo | Pergunta corrigida substitui a anterior; não envia histórico; base selecionada por tarefa | TRH-01 recebe toda a pequena política; não há memória entre rodadas |
| Saída estruturada | JSON com chaves, categoria, confiança numérica e motivo; rejeita listas, nulos e booleanos em confiança | Não comprova correção semântica da rota |
| Validação do especialista | Campos não vazios e classificação permitida | Factualidade e autoridade exigem revisão humana |
| Recuperação de falhas | No máximo uma repetição total entre triagem e especialista; timeout e falha de conexão geram retorno seguro | Não há retry infinito nem estimativa de tokens/custos |
| 13 casos | Aba Testes carrega `tests/casos.csv`, com cópia de apresentação sincronizada por teste | Execuções reais e avaliação ainda precisam ser salvas |
| Evidências | CSV e JSON com ID/data, pergunta/correção, modo, modelo, parâmetros, rota, prompt/versão, resposta, contexto, tentativas, validação, latência e avaliação humana | Apenas na memória da página até exportar |
| Baseline T2 | Sete perguntas originais na UI; métricas usam a primeira execução real de cada caso | Métricas ficam pendentes até execução/revisão; outro modelo sinaliza divergência sem sobrescrever evidências |

## Demonstração para o professor

1. Abrir **Trabalho 4** e conferir modelo, base e biblioteca.
2. Executar uma pergunta de regras, elegibilidade e segurança; inspecionar a rota e o prompt em cada resposta.
3. Carregar D1 e demonstrar a pergunta de esclarecimento; usar **Corrigir ou complementar minha pergunta** com a função incluída na pergunta completa.
4. Carregar A1 e F1 para demonstrar ambiguidade e recusa.
5. Executar E1 e E2: as chamadas são simuladas, mas passam pelo mesmo orquestrador e validadores usados nas chamadas reais. O modo é identificado na tela e nos arquivos exportados.
6. Registrar a revisão humana em cada resultado, exportar CSV/JSON e completar a comparação dos sete casos do baseline.

Repetições preservam os registros anteriores. Corrigir/editar uma pergunta transforma
a nova execução em pergunta livre para não atribuí-la indevidamente ao caso original.
O chat RAG continua acessível em aba separada; uploads não alteram a base dos testes T4.

## Continuidade dos trabalhos anteriores

- T1/T2: mantém o caso Aurora Tech e a base da política-piloto.
- T2: mantém as métricas do baseline como referência de comparação.
- T3: utiliza TRH-01 v0.3, TRH-02 v0.1, TRH-03 v0.1 e TRH-04 v0.1.
- T4: integra os templates em um fluxo executável e adiciona validação e repetição controlada.

## Observação de rastreabilidade

O ZIP recebido não continha os arquivos textuais dos quatro templates do T3. Por isso, os arquivos em `BACKEND/prompts/templates/` foram reconstruídos de forma conservadora a partir do relatório do T3: IDs, versões ativas, finalidades, formatos de saída, regra contra extrapolação e few-shot do TRH-01. Eles devem ser comparados com os prompts originais do T3, caso o grupo possua esses arquivos em outro local, antes da entrega final.

A base em `BACKEND/knowledge/politica_aurora_tech.txt` reproduz a base de conhecimento apresentada no material do T2.

## Testes

`BACKEND/tests/test_t4_flow.py` e `test_t4_api.py` cobrem roteamento, contratos JSON,
dado ausente, baixa confiança, fora do escopo, substituição da pergunta por correção,
contexto por tarefa, timeout, orçamento único de repetição e simulações da API.
Os testes da feature React cobrem envio real/simulado, revisão pendente, correção,
erro de rede, exportação CSV e preservação da primeira tentativa nas métricas.
Esses testes automatizados são determinísticos, sem chamadas reais ao modelo, e não
substituem as evidências acadêmicas da avaliação.

Os 13 casos acadêmicos estão em `tests/casos.csv`. `tests/resultados.csv` foi criado com `PENDENTE` porque resultados reais, latências e saídas do modelo não devem ser inventados.

## Próxima etapa obrigatória

Executar os 13 casos com o ambiente real e reaplicar os sete casos originais do T2. Salvar evidências e preencher `tests/resultados.csv` e `evaluation/comparacao_baseline.md`.
