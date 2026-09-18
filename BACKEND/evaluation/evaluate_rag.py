"""Avaliação local e reproduzível da recuperação do MVP."""

import json
from pathlib import Path
from typing import TypedDict

from app.core.config import Settings
from app.services.documents import DocumentProcessor, DocumentService
from app.services.embeddings import OpenRouterEmbeddingService
from app.services.rag import RetrievalService
from tests.fakes import InMemoryVectorStore


class EvaluationCase(TypedDict):
    question: str
    expected_source: str | None


class EvaluationDocument(TypedDict):
    name: str
    content: str


def main() -> int:
    dataset_path = Path(__file__).with_name("rag_cases.json")
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases: list[EvaluationCase] = dataset["cases"]
    documents: list[EvaluationDocument] = dataset["documents"]

    settings = Settings()
    embeddings = OpenRouterEmbeddingService(settings)
    store = InMemoryVectorStore()
    document_service = DocumentService(
        processor=DocumentProcessor(settings),
        embedding_service=embeddings,
        vector_store=store,
    )
    retrieval = RetrievalService(
        settings=settings,
        embedding_service=embeddings,
        vector_store=store,
    )

    for document in documents:
        document_service.index_document(
            filename=document["name"],
            content=document["content"].encode(),
            content_type="text/plain",
        )

    passed = 0
    results = []
    for case in cases:
        chunks = retrieval.retrieve(case["question"])
        sources = [chunk.document_name for chunk in chunks]
        expected = case["expected_source"]
        success = expected in sources if expected is not None else not chunks
        passed += int(success)
        results.append(
            {
                "question": case["question"],
                "expected_source": expected,
                "retrieved_sources": sources,
                "top_relevance": round(chunks[0].relevance, 3) if chunks else None,
                "passed": success,
            }
        )

    print(json.dumps({"passed": passed, "total": len(cases), "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
