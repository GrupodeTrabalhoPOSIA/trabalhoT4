-- Executar somente com a base vazia e uploads pausados.
begin;
set local lock_timeout = '5s';

lock table public.aurora_documents, public.aurora_document_chunks
    in access exclusive mode;

do $guard$
begin
    if exists (select 1 from public.aurora_documents)
        or exists (select 1 from public.aurora_document_chunks) then
        raise exception 'A troca de modelo exige uma base vazia. Nenhum dado foi apagado.';
    end if;
end;
$guard$;

drop index if exists public.aurora_document_chunks_embedding_hnsw_idx;

alter table public.aurora_document_chunks
    alter column embedding type extensions.vector(384)
    using embedding::extensions.vector(384);

create index aurora_document_chunks_embedding_hnsw_idx
    on public.aurora_document_chunks
    using hnsw (embedding extensions.vector_cosine_ops);

create or replace function public.match_aurora_chunks(
    query_embedding extensions.vector(384),
    match_threshold double precision default 0.35,
    match_count integer default 5
)
returns table (
    document_id uuid,
    document_name text,
    content text,
    chunk_index integer,
    page integer,
    similarity double precision
)
language sql
stable
security invoker
set search_path = ''
as $function$
    select
        chunk.document_id,
        document.name as document_name,
        chunk.content,
        chunk.chunk_index,
        chunk.page,
        (1 - (chunk.embedding operator(extensions.<=>) query_embedding))::double precision as similarity
    from public.aurora_document_chunks as chunk
    inner join public.aurora_documents as document on document.id = chunk.document_id
    where 1 - (chunk.embedding operator(extensions.<=>) query_embedding) >= match_threshold
    order by chunk.embedding operator(extensions.<=>) query_embedding
    limit least(greatest(match_count, 1), 20);
$function$;

revoke all on function public.match_aurora_chunks(extensions.vector, double precision, integer)
    from public, anon, authenticated;
grant execute on function public.match_aurora_chunks(extensions.vector, double precision, integer)
    to service_role;

commit;
