begin;

drop function if exists public.match_aurora_chunks(
    extensions.vector,
    double precision,
    integer
);
drop function if exists public.index_aurora_document(
    uuid,
    text,
    text,
    text,
    bigint,
    jsonb
);
drop table if exists public.aurora_document_chunks;
drop table if exists public.aurora_documents;

commit;
