"""Candidata multimodal: recuperação isolada por anexo e fluxo textual preservado."""
import math
import hashlib
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

import pymupdf
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.api.dependencies import get_embedding_service
from app.api.v1.routes.t4 import SimulatedClient, get_t4_service
from app.core.config import get_settings
from app.core.errors import AppError
from app.services.documents import DocumentProcessor
from app.services.t4.flow import PROMPT_VERSIONS, T4FlowService
from app.services.final_delivery import current_release_id

router = APIRouter(prefix="/t5", tags=["Trabalho 5"])
CANDIDATE = "t5-v1"
MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 20
MAX_CHARACTERS = 30000


def retrieve_document(filename, content, content_type, question):
    """Nenhum documento, texto ou vetor é persistido no servidor ou no Supabase."""
    if Path(filename).suffix.lower() == ".pdf":
        try:
            with pymupdf.open(stream=content, filetype="pdf") as pdf:
                if len(pdf) > MAX_PAGES:
                    raise AppError(status_code=422, code="PAGE_LIMIT", message="Use um PDF com até 20 páginas.")
        except AppError:
            raise
        except Exception:
            raise AppError(status_code=422, code="INVALID_PDF", message="Não foi possível ler o PDF. Envie um arquivo válido com texto selecionável.") from None
    document = DocumentProcessor().process(filename=filename, content=content, content_type=content_type)
    characters = sum(len(chunk.content) for chunk in document.chunks)
    if characters < 40:
        raise AppError(status_code=422, code="LOW_QUALITY", message="Texto insuficiente: envie uma política legível com pelo menos 40 caracteres.")
    if characters > MAX_CHARACTERS:
        raise AppError(status_code=422, code="TEXT_LIMIT", message="O texto extraído excede 30.000 caracteres, incluindo sobreposições. Envie um documento menor.")
    embeddings = get_embedding_service()
    vectors = embeddings.embed_documents([chunk.content for chunk in document.chunks])
    query = embeddings.embed_query(question)
    query_norm = math.sqrt(sum(value * value for value in query))
    settings = get_settings()
    ranked = []
    for chunk, vector in zip(document.chunks, vectors, strict=True):
        norm = math.sqrt(sum(value * value for value in vector)) * query_norm
        score = sum(a * b for a, b in zip(query, vector, strict=True)) / norm if norm else 0
        if score >= settings.retrieval_min_relevance:
            ranked.append({"document_name": document.name, "document_hash": document.content_hash, "chunk_index": chunk.chunk_index, "page": chunk.page, "content": chunk.content, "relevance": round(score, 4)})
    ranked.sort(key=lambda item: item["relevance"], reverse=True)
    selected, size = [], 0
    for item in ranked[:settings.retrieval_top_k]:
        if size + len(item["content"]) <= settings.max_context_characters:
            selected.append(item)
            size += len(item["content"])
    return selected, {"name": document.name, "sha256": document.content_hash, "size_bytes": document.file_size, "chunks": len(document.chunks), "quality": "Texto extraível; legibilidade e completude exigem revisão humana."}


@router.get("/config")
def configuration():
    settings = get_settings()
    return {"candidate": CANDIDATE, "model": settings.openrouter_model, "max_bytes": MAX_BYTES, "max_pages": MAX_PAGES, "max_characters": MAX_CHARACTERS, "formats": [".pdf", ".docx", ".txt", ".md"], "top_k": settings.retrieval_top_k, "min_relevance": settings.retrieval_min_relevance, "embedding_model": settings.openrouter_embedding_model, "max_context_characters": settings.max_context_characters, "temperature": settings.openrouter_temperature, "max_tokens": settings.openrouter_max_tokens, "chunk_size": settings.chunk_size, "chunk_overlap": settings.chunk_overlap, "prompts": PROMPT_VERSIONS, "timeout_seconds": settings.openrouter_timeout_seconds, "embedding_dimensions": settings.embedding_dimensions, "embedding_batch_size": settings.embedding_batch_size, "upload_limit_mb": settings.max_upload_size_mb}


@router.post("/run")
async def run_flow(
    service: Annotated[T4FlowService, Depends(get_t4_service)],
    question: Annotated[str, Form(min_length=1, max_length=2000)],
    mode: Annotated[Literal["real", "invalid_router", "invalid_specialist"], Form()] = "real",
    file: Annotated[UploadFile | None, File()] = None,
):
    if not question.strip():
        raise AppError(status_code=422, code="EMPTY_QUESTION", message="Informe uma pergunta.")
    if file is not None and mode != "real":
        await file.close()
        raise AppError(status_code=422, code="INVALID_SIMULATION", message="Simulações textuais não aceitam anexos.")
    started = time.perf_counter()
    sources, document = [], None
    metadata = {"execution_id": str(uuid4()), "executed_at": datetime.now(timezone.utc).isoformat(), "candidate": CANDIDATE, "question": question.strip(), "mode": mode, "model": get_settings().openrouter_model if mode == "real" else "simulação determinística", "configuration": configuration(), "origin": "t5", "release_id": current_release_id()}
    try:
        context = None
        if file is not None:
            try:
                content = await file.read(MAX_BYTES + 1)
            finally:
                await file.close()
            if len(content) > MAX_BYTES:
                raise AppError(status_code=413, code="FILE_TOO_LARGE", message="Envie um arquivo de até 10 MB.")
            document = {"name": Path(file.filename or "").name, "sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content), "chunks": 0, "quality": "Extração não concluída."}
            sources, document = await run_in_threadpool(retrieve_document, file.filename or "", content, file.content_type, question)
            context = "\n\n".join(f"[Fonte: {item['document_name']}; SHA-256: {item['document_hash']}; página: {item['page'] or 'n/a'}; trecho: {item['chunk_index'] + 1}]\n{item['content']}" for item in sources)
        if context == "":
            result = {"answer": "Resposta: Não encontrei evidência suficiente no documento.\nRegra aplicada: Nenhum trecho atingiu o limiar de recuperação.\nPróximo passo: Confira o documento e reformule a pergunta.", "route": "FORA_ESCOPO", "prompt_id": "RECUPERAÇÃO", "prompt_version": "v1", "valid": True, "retries": 0, "status": "sem_evidencia", "trace": [], "attempts": [], "context": ""}
        else:
            if mode != "real":
                service = T4FlowService(llm_client=SimulatedClient(mode), prompt_registry=service.prompts, knowledge_base=service.knowledge_base)
            result = asdict(await service.run(question, evidence_context=context))
        if file is not None:
            result["trace"] = [{"id": "document", "state": "completed", "detail": "Arquivo validado e texto extraído; sem persistência na base compartilhada."}, {"id": "retrieval", "state": "completed" if sources else "warning", "detail": f"{len(sources)} trechos recuperados apenas deste anexo."}, *result["trace"]]
        return {**result, **metadata, "sources": sources, "document": document, "latency_ms": round((time.perf_counter() - started) * 1000), "error_code": None}
    except AppError as error:
        message = error.message
        if error.code == "EMPTY_DOCUMENT":
            message += " Envie uma versão legível com texto selecionável; este protótipo não faz OCR."
        return {**metadata, "answer": message, "route": "FORA_ESCOPO", "prompt_id": "ENTRADA", "prompt_version": "v1", "valid": False, "retries": 0, "status": "entrada_rejeitada" if error.status_code < 500 and error.code not in {"MODEL_CREDIT_LIMIT", "MODEL_RATE_LIMITED"} else "falha_servico", "trace": [], "attempts": [], "context": "", "sources": sources, "document": document, "latency_ms": round((time.perf_counter() - started) * 1000), "error_code": error.code}
