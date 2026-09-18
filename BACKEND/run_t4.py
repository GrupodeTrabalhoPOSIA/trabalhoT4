"""Executa o protótipo textual do Trabalho 4 no terminal."""
import asyncio
from pathlib import Path

from app.core.config import Settings
from app.services.llm import OpenRouterClient
from app.services.t4 import PromptRegistry, T4FlowService

ROOT = Path(__file__).resolve().parent

async def main() -> None:
    settings = Settings()
    service = T4FlowService(
        llm_client=OpenRouterClient(settings),
        prompt_registry=PromptRegistry(ROOT / "prompts" / "templates"),
        knowledge_base=(ROOT / "knowledge" / "politica_aurora_tech.txt").read_text(encoding="utf-8"),
    )
    print("Aurora Tech — protótipo T4. Digite 'sair' para encerrar.")
    while True:
        question = input("\nVocê: ").strip()
        if question.lower() == "sair":
            break
        result = await service.run(question)
        print(f"\nCopiloto: {result.answer}")
        print(f"[rota={result.route}; prompt={result.prompt_id} {result.prompt_version}; validação={result.valid}; repetições={result.retries}; latência={result.latency_ms} ms; status={result.status}]")

if __name__ == "__main__":
    asyncio.run(main())
