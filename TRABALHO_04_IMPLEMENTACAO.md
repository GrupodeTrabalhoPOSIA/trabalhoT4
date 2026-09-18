# Trabalho 4 — Fluxo de Geração e Protótipo Textual

## O que foi incorporado

O repositório existente foi preservado. O T4 foi acrescentado como uma camada de orquestração em `BACKEND/app/services/t4/`, sem remover o chatbot RAG anterior.

O fluxo implementado segue: entrada → validação → TRH-04 → verificação de dados → carregamento do template/versionamento → contexto mínimo → modelo → validação → resposta, pergunta, recusa/encaminhamento ou fallback.

## Continuidade dos trabalhos anteriores

- T1/T2: mantém o caso Aurora Tech e a base da política-piloto.
- T2: mantém as métricas do baseline como referência de comparação.
- T3: utiliza TRH-01 v0.3, TRH-02 v0.1, TRH-03 v0.1 e TRH-04 v0.1.
- T4: integra os templates em um fluxo executável e adiciona validação e repetição controlada.

## Observação de rastreabilidade

O ZIP recebido não continha os arquivos textuais dos quatro templates do T3. Por isso, os arquivos em `BACKEND/prompts/templates/` foram reconstruídos de forma conservadora a partir do relatório do T3: IDs, versões ativas, finalidades, formatos de saída, regra contra extrapolação e few-shot do TRH-01. Eles devem ser comparados com os prompts originais do T3, caso o grupo possua esses arquivos em outro local, antes da entrega final.

A base em `BACKEND/knowledge/politica_aurora_tech.txt` reproduz a base de conhecimento apresentada no material do T2.

## Testes

`BACKEND/tests/test_t4_flow.py` contém testes automatizados determinísticos, sem chamada de rede, para roteamento, dado ausente, fora do escopo, JSON inválido, correção controlada e fallback.

Os 13 casos acadêmicos estão em `tests/casos.csv`. `tests/resultados.csv` foi criado com `PENDENTE` porque resultados reais, latências e saídas do modelo não devem ser inventados.

## Próxima etapa obrigatória

Executar os 13 casos com o ambiente real e reaplicar os sete casos originais do T2. Salvar evidências e preencher `tests/resultados.csv` e `evaluation/comparacao_baseline.md`.
