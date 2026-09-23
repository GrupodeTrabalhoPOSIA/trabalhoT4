# Configuração das integrações

## Revisão de 22/09/2026

- Produção: `/api/v1/t4/config` responde e informa `mistralai/mistral-large`. A chamada T4 examinada recebeu 429 do OpenRouter nas duas tentativas, com origem normalizada como provedor. Esse retorno não prova falta de saldo.
- O preflight CORS da API publicada aceita `https://trabalhos-aaplicacoes-llms-posia-pucmg.vercel.app`.
- O bundle específico do T4 publicado contém o aviso de diagnóstico do serviço. Ele é carregado separadamente do bundle principal. A imagem sem esse aviso não permite concluir que o frontend esteja desatualizado; execuções sem os campos de diagnóstico não mostram esse alerta.
- Local: existe `env` na raiz, mas não `BACKEND/.env` nem `FRONTEND/.env`. O arquivo `env` não é carregado automaticamente. A chave dele retornou 401 tanto em `/api/v1/key` quanto em `/api/v1/chat/completions`. É necessário substituir essa credencial para testar localmente. Nenhuma chave foi copiada para este documento.
- Na revisão inicial, o arquivo local informava `openai/gpt-4o-mini`. Agora `OPENROUTER_MODEL` é obrigatório, sem padrão no código; o valor do ambiente é respeitado. Configure `mistralai/mistral-large` para este projeto.
- Os valores secretos efetivamente cadastrados no Render não foram inspecionados; não é possível afirmar que a chave local seja a mesma da produção.

## Variáveis por ambiente

| Variável | Local | Produção | Finalidade |
| --- | --- | --- | --- |
| `VITE_API_URL` | `FRONTEND/.env`: `http://localhost:8000/api/v1` | Vercel: `https://trabalhot4-1.onrender.com/api/v1` | Endereço público da API; exige novo build do frontend. |
| `OPENROUTER_API_KEY` | `BACKEND/.env`: chave válida | Render Environment: chave válida | Autenticação; nunca enviar ao frontend ou versionar. |
| `OPENROUTER_MODEL` | `mistralai/mistral-large` | Mesmo valor no Render | Obrigatório, sem padrão no código; valor usado nas chamadas. |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Render: `https://trabalhos-aaplicacoes-llms-posia-pucmg.vercel.app` | CORS: origem exata, sem barra final, caminho ou fragmento. |
| `OPENROUTER_REFERER` | `http://localhost:5173` | Render: URL pública do frontend | Identificação opcional no OpenRouter; não autentica nem libera cotas. |
| `OPENROUTER_APP_TITLE` | `Aurora Tech Chatbot` | Mesmo valor no Render | Identificação opcional. |
| `OPENROUTER_EMBEDDING_MODEL` | `mistralai/mistral-embed-2312` | Mesmo valor no Render | Obrigatório, sem padrão no código; embeddings usados na busca de documentos. |
| `EMBEDDING_DIMENSIONS` | `1024` | `1024` no Render | Dimensão esperada dos vetores; deve corresponder ao modelo e ao índice do banco. |
| `SUPABASE_DB_URL` | `BACKEND/.env`: URI secreta do Session Pooler | Render Environment: URI secreta do Session Pooler | PostgreSQL, porta 5432; necessário para documentos/RAG e para as migrações do Docker. |

Os demais parâmetros têm defaults em `BACKEND/.env.example`: timeout de 30 s, 500 tokens e temperatura 0.1. O T4 não consulta o Supabase durante a execução, mas o Docker atual executa migrações antes de iniciar a API e precisa do banco configurado.

O backend resolve o `.env` relativo à instalação do backend, sem depender do diretório do terminal. Em execução local com a árvore fonte, isso corresponde a `BACKEND/.env`. Na imagem Docker, use as variáveis de ambiente do Render; arquivos `.env` não são copiados para a imagem. Variáveis do processo têm prioridade sobre o arquivo.

`BASELINE_MODEL` identifica o modelo usado nas evidências históricas do T2; configure `mistralai/mistral-large` para esse baseline. Sem essa variável, a comparação fica pendente. Não altere o modelo histórico só porque mudou o modelo de geração.

`EMBEDDING_SEND_DIMENSIONS=false` omite o parâmetro `dimensions` da chamada. Use `true` somente com modelos que aceitem esse parâmetro. `EMBEDDING_DIMENSIONS` continua validando o tamanho do vetor recebido. A troca de modelo de embeddings exige reindexar documentos e conferir a dimensão do índice; vetores de modelos diferentes não são intercambiáveis.

Tanto `OPENROUTER_MODEL` quanto `OPENROUTER_EMBEDDING_MODEL` são obrigatórios. O frontend obtém os modelos pela API, sem modelos padrão no bundle. Nomes em relatórios históricos e fixtures de teste representam as respectivas evidências, não escolhem modelos de execução.

## Verificação segura

Crie `BACKEND/.env` a partir de `BACKEND/.env.example` e `FRONTEND/.env` a partir de `FRONTEND/.env.example`. Preencha a chave válida e a URI do banco somente no backend. O arquivo antigo `env` da raiz não deve ser adotado sem revisão: sua chave foi rejeitada e o modelo está divergente.

No diretório `BACKEND`:

```powershell
.venv/Scripts/python.exe -m app.check_integrations
.venv/Scripts/python.exe -m app.check_integrations --live
```

O primeiro comando apenas confere a configuração. O segundo valida a chave e, somente se aceita, faz uma chamada sintética ao modelo; pode consumir créditos. Não imprime credenciais, URI do banco, corpo bruto ou texto gerado. Para conferir um arquivo específico, acrescente `--env-file caminho`. No shell do Render, use `python -m app.check_integrations --live` após publicar a versão com esse comando.

401 exige corrigir a credencial. 402 indica limite financeiro. 429 exige verificar o limite/cota/capacidade informado pelo provedor e as configurações da conta; não se deve trocar a chave ou o modelo automaticamente. `/health` confirma apenas que a API está em execução, não que OpenRouter e Supabase funcionam.

Depois de corrigir as variáveis, reinicie/republique o backend e faça novo build do frontend. Antes de publicar código alterado, regenere o manifesto T6 com `python evaluation/freeze_final.py` e reexecute os casos exigidos pelo projeto. Uma nova release não aprova automaticamente evidências anteriores.

Referências: [contrato HTTP e headers](https://openrouter.ai/docs/api_reference/overview), [erros do provedor](https://openrouter.ai/docs/api_reference/errors-and-debugging), [limites e validação da chave](https://openrouter.ai/docs/api_reference/limits).
