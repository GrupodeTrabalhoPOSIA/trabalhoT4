# Avaliação RAG do MVP

Esta avaliação verifica a recuperação de fontes antes da chamada ao modelo. Ela usa o modelo real de embeddings configurado e um armazenamento isolado em memória, sem escrever no projeto Supabase, com três perguntas respondíveis e uma pergunta sem relação com a base.

## Resultado de referência anterior

Em 27/08/2026, ainda com o modelo local anterior, `python evaluation/evaluate_rag.py` aprovou 4 de 4 casos:

- serviços oferecidos → `servicos.txt`;
- horário comercial → `servicos.txt`;
- missão da empresa → `empresa.txt`;
- previsão do tempo em Marte → recusada sem contexto.

## Parâmetros finais

- modelo: `mistralai/mistral-embed-2312`, via OpenRouter, com 1024 dimensões;
- tamanho do chunk: 700 caracteres;
- sobreposição: 100 caracteres;
- `top_k`: 5;
- relevância mínima: 0,35;
- contexto máximo: 6.000 caracteres.

O limiar 0,35 preservou a pergunta conhecida com menor pontuação observada (0,38) e rejeitou o caso negativo no modelo anterior. Esse limiar deve ser recalibrado depois da primeira execução com o modelo do OpenRouter. A base é deliberadamente pequena e acadêmica; uma implantação real exigiria um conjunto de avaliação maior e revisão periódica desses valores.

## Execução

```powershell
python evaluation/evaluate_rag.py
```

A execução requer `OPENROUTER_API_KEY` em `BACKEND/.env` e consome créditos para indexar os documentos de avaliação e gerar os embeddings das perguntas.
