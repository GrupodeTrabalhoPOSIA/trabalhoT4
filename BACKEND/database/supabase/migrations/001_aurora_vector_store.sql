begin;

create extension if not exists vector with schema extensions;

create table if not exists public.aurora_documents (
    id uuid primary key,
    name text not null,
    document_type text not null,
    content_hash text not null unique,
    file_size bigint not null check (file_size >= 0),
    chunk_count integer not null check (chunk_count > 0),
    created_at timestamptz not null default now()
);

create table if not exists public.aurora_document_chunks (
    id uuid primary key,
    document_id uuid not null references public.aurora_documents(id) on delete cascade,
    content text not null,
    chunk_index integer not null check (chunk_index >= 0),
    page integer,
    embedding extensions.vector(384) not null,
    unique (document_id, chunk_index)
);

create index if not exists aurora_document_chunks_embedding_hnsw_idx
    on public.aurora_document_chunks
    using hnsw (embedding extensions.vector_cosine_ops);

create index if not exists aurora_document_chunks_document_id_idx
    on public.aurora_document_chunks (document_id);

create or replace function public.index_aurora_document(
    p_id uuid,
    p_name text,
    p_document_type text,
    p_content_hash text,
    p_file_size bigint,
    p_chunks jsonb
)
returns table (
    id uuid,
    name text,
    document_type text,
    chunk_count integer,
    file_size bigint,
    created_at timestamptz
)
language plpgsql
security invoker
set search_path = ''
as $function$
declare
    v_chunk_count integer;
begin
    if jsonb_typeof(p_chunks) is distinct from 'array' then
        raise exception 'p_chunks deve ser um array JSON';
    end if;

    v_chunk_count := jsonb_array_length(p_chunks);
    if v_chunk_count = 0 then
        raise exception 'o documento deve possuir ao menos um chunk';
    end if;

    insert into public.aurora_documents (
        id,
        name,
        document_type,
        content_hash,
        file_size,
        chunk_count
    ) values (
        p_id,
        p_name,
        p_document_type,
        p_content_hash,
        p_file_size,
        v_chunk_count
    );

    insert into public.aurora_document_chunks (
        id,
        document_id,
        content,
        chunk_index,
        page,
        embedding
    )
    select
        (chunk->>'id')::uuid,
        p_id,
        chunk->>'content',
        (chunk->>'chunk_index')::integer,
        case
            when chunk->>'page' is null then null
            else (chunk->>'page')::integer
        end,
        (chunk->'embedding')::text::extensions.vector
    from jsonb_array_elements(p_chunks) as chunk;

    return query
    select
        document.id,
        document.name,
        document.document_type,
        document.chunk_count,
        document.file_size,
        document.created_at
    from public.aurora_documents as document
    where document.id = p_id;
end;
$function$;

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

alter table public.aurora_documents enable row level security;
alter table public.aurora_document_chunks enable row level security;

revoke all on table public.aurora_documents from anon, authenticated;
revoke all on table public.aurora_document_chunks from anon, authenticated;
revoke all on function public.index_aurora_document(uuid, text, text, text, bigint, jsonb)
    from public, anon, authenticated;
revoke all on function public.match_aurora_chunks(extensions.vector, double precision, integer)
    from public, anon, authenticated;

grant select, insert, update, delete on table public.aurora_documents to service_role;
grant select, insert, update, delete on table public.aurora_document_chunks to service_role;
grant execute on function public.index_aurora_document(uuid, text, text, text, bigint, jsonb)
    to service_role;
grant execute on function public.match_aurora_chunks(extensions.vector, double precision, integer)
    to service_role;

commit;
