# Banco Supabase

O backend usa o Postgres do Supabase com a extensão `pgvector`. O React não acessa o banco diretamente.

## Aplicar a estrutura

1. Crie um projeto no Supabase.
2. Abra **SQL Editor** no painel.
3. Copie e execute `migrations/001_aurora_vector_store.sql` e depois `migrations/002_mistral_embeddings_1024.sql`, nessa ordem. Se a primeira já foi aplicada, execute somente a segunda.
4. Abra **Connect**, selecione **Session pooler** e copie a URI PostgreSQL.
5. Substitua `[YOUR-PASSWORD]` pela senha do banco e configure a URI como `SUPABASE_DB_URL` no backend.

A URI de Session Pooler usa o formato abaixo e a porta `5432`:

```dotenv
SUPABASE_DB_URL=postgresql://postgres.PROJECT_REF:SENHA@aws-0-REGIAO.pooler.supabase.com:5432/postgres
```

Se a senha tiver caracteres reservados de URL, codifique-os antes de montar a URI. `SUPABASE_POOL_MIN_SIZE` e `SUPABASE_POOL_MAX_SIZE` controlam quantas sessões o processo mantém; os padrões acadêmicos são 1 e 5.

A migração pode ser executada novamente sem recriar tabelas ou índices. Ela cria duas tabelas, a função transacional de indexação e a função de busca por similaridade cosseno.

A migração 002 muda a coluna para `vector(1024)`, compatível com `mistralai/mistral-embed-2312`. Ela bloqueia escritas durante a transação e recusa a execução se houver documentos ou chunks; nenhum registro é apagado. Pause uploads, aplique a migração, configure o backend com o modelo Mistral e `EMBEDDING_DIMENSIONS=1024` e só então reabra os uploads. Não reaplique a 001 isoladamente após a 002.

Para conferir o resultado no SQL Editor:

```sql
select format_type(atttypid, atttypmod) as embedding_type
from pg_attribute
where attrelid = 'public.aurora_document_chunks'::regclass
  and attname = 'embedding';
```

O resultado deve ser `extensions.vector(1024)` ou `vector(1024)`, dependendo do search path. Trocar de modelo com documentos existentes exige reindexação; vetores de modelos diferentes não podem ser misturados.

## Segurança

As tabelas usam RLS e não concedem acesso aos papéis `anon` e `authenticated`. A URI contém a senha do Postgres e deve existir somente no backend e nas variáveis secretas do serviço de hospedagem. O frontend não usa credenciais Supabase.

## Reversão

`rollback/002_mistral_embeddings_1024.sql` restaura 384 dimensões somente se a base continuar vazia. Depois da reversão, restaure também o modelo anterior e `EMBEDDING_DIMENSIONS=384` no backend. O índice vetorial é recriado; nenhum documento é excluído.

O script `rollback/001_aurora_vector_store.sql` remove as funções, os documentos e todos os embeddings. Use-o apenas quando a perda desses dados for intencional.
