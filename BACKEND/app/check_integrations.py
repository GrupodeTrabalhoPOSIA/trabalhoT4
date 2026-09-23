"""Diagnóstico administrativo local: nunca imprime chaves, URIs ou respostas brutas."""

import argparse
import asyncio
import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import AppError
from app.services.llm.openrouter import OpenRouterClient


async def check(settings: Settings, *, live: bool = False) -> dict:
    report = {
        "model": settings.openrouter_model,
        "embedding_model": settings.openrouter_embedding_model,
        "openrouter_key_configured": settings.openrouter_api_key is not None,
        "supabase_configured": settings.supabase_db_url is not None,
        "frontend_origin": settings.frontend_origin,
        "remote_checks": "not_requested",
    }
    if not live:
        return report
    if settings.openrouter_api_key is None:
        report["remote_checks"] = "MODEL_NOT_CONFIGURED"
        return report
    try:
        async with httpx.AsyncClient(timeout=settings.openrouter_timeout_seconds) as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/key",
                headers={"Authorization": f"Bearer {settings.require_openrouter_api_key()}"},
            )
        report["key_http_status"] = response.status_code
        if not response.is_success:
            report["remote_checks"] = "key_check_failed"
            return report
        # Uma chamada curta e sintética; sem retries nem envio de documentos.
        await OpenRouterClient(settings).complete([
            {"role": "user", "content": "Responda apenas OK."},
        ])
        report["remote_checks"] = "chat_ok"
    except AppError as error:
        report["remote_checks"] = error.code
        if error.diagnostic:
            report["diagnostic"] = error.diagnostic.model_dump(exclude_none=True)
    except httpx.RequestError:
        report["remote_checks"] = "connection_failed"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, help="Arquivo explícito; padrão: BACKEND/.env.")
    parser.add_argument("--live", action="store_true", help="Valida a chave e chama o modelo; pode consumir créditos.")
    args = parser.parse_args()
    if args.env_file is not None and not args.env_file.is_file():
        print('{"configuration_error": "env_file_not_found"}')
        return 1
    try:
        settings = Settings(_env_file=args.env_file) if args.env_file is not None else Settings()
    except ValidationError as error:
        # str(error) pode conter input_value com segredos.
        print(json.dumps({"configuration_error_fields": [list(e["loc"]) for e in error.errors()]}))
        return 1
    report = asyncio.run(check(settings, live=args.live))
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return int(args.live and report["remote_checks"] != "chat_ok")


if __name__ == "__main__":
    raise SystemExit(main())
