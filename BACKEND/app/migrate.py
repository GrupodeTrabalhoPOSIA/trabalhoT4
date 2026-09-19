"""Aplica migrações versionadas antes de iniciar a API Docker."""

import hashlib
import logging
from pathlib import Path

import psycopg

from app.core.config import get_settings


def migration_body(sql: str) -> str:
    """Remove somente a transação externa dos scripts manuais existentes."""
    lines = sql.splitlines()
    meaningful = [i for i, line in enumerate(lines) if line.strip() and not line.lstrip().startswith("--")]
    if not meaningful or lines[meaningful[0]].strip().lower() != "begin;" or lines[meaningful[-1]].strip().lower() != "commit;":
        raise ValueError("Migração deve conter BEGIN e COMMIT externos.")
    lines[meaningful[0]] = ""
    lines[meaningful[-1]] = ""
    return "\n".join(lines)


def migrate(directory: Path) -> None:
    files = sorted(directory.glob("[0-9]*.sql"))
    if not files:
        raise RuntimeError("Scripts de migração ausentes na imagem.")
    url = get_settings().require_supabase_database_url()
    with psycopg.connect(url, autocommit=True, connect_timeout=15) as connection:
        # Lock de sessão: protege deploys concorrentes, inclusive entre transações.
        connection.execute("SET statement_timeout = '120s'")
        connection.execute("SELECT pg_advisory_lock(719042601)")
        try:
            with connection.transaction():
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS public.aurora_schema_migrations (
                        name text PRIMARY KEY,
                        checksum text NOT NULL,
                        applied_at timestamptz NOT NULL DEFAULT now()
                    )
                """)
                connection.execute("ALTER TABLE public.aurora_schema_migrations ENABLE ROW LEVEL SECURITY")
                connection.execute("REVOKE ALL ON public.aurora_schema_migrations FROM PUBLIC, anon, authenticated")
            for path in files:
                sql = path.read_text(encoding="utf-8")
                checksum = hashlib.sha256(sql.replace("\r\n", "\n").encode()).hexdigest()
                with connection.transaction():
                    applied = connection.execute(
                        "SELECT checksum FROM public.aurora_schema_migrations WHERE name = %s", (path.name,)
                    ).fetchone()
                    if applied:
                        if applied[0] != checksum:
                            raise RuntimeError(f"Migração aplicada foi modificada: {path.name}")
                        continue
                    if path == files[0] and connection.execute(
                        "SELECT to_regclass('public.aurora_documents'), to_regclass('public.aurora_document_chunks')"
                    ).fetchone() != (None, None):
                        raise RuntimeError("Banco já contém estrutura sem histórico. Valide as migrações manuais antes de adotar o runner; nenhum dado foi apagado.")
                    connection.execute(migration_body(sql))
                    connection.execute(
                        "INSERT INTO public.aurora_schema_migrations (name, checksum) VALUES (%s, %s)",
                        (path.name, checksum),
                    )
                logging.info("Migração aplicada: %s", path.name)
        finally:
            connection.execute("SELECT pg_advisory_unlock(719042601)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        migrate(Path("database/supabase/migrations"))
    except Exception as error:
        # Não imprime URI, senha ou detalhes de conexão nos logs públicos.
        logging.error("Migrações falharam (%s). Verifique conexão, permissões e histórico do banco.", type(error).__name__)
        raise SystemExit(1) from None
