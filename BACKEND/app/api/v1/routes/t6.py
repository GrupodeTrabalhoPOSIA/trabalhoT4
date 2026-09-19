"""Entrega final: executar, auditar e empacotar uma versão identificada."""
import io
from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from starlette.datastructures import Headers

from app.api.v1.routes.t4 import get_t4_service
from app.api.v1.routes.t5 import run_flow
from app.core.errors import AppError
from app.models.final_delivery import DeliveryInput, ExecuteCase
from app.services.final_delivery import RELEASE_ROOT, SCENES, audit, release_state
from app.services.final_package import build_package, presentation
from app.services.t4.flow import T4FlowService

router = APIRouter(prefix="/t6", tags=["Entrega final"])

def require_frozen(state, release_id=None):
    if not state["frozen"] or release_id != state["manifest"]["release_id"]:
        raise AppError(status_code=409, code="RELEASE_MISMATCH", message="Versão divergente ou não congelada. Gere e publique o mesmo manifesto no frontend e backend antes de continuar.")

@router.get("/manifest")
def manifest():
    return release_state()

@router.post("/audit")
def evaluate(data: DeliveryInput):
    return audit(data)

@router.post("/run")
async def execute(request: ExecuteCase, service: Annotated[T4FlowService, Depends(get_t4_service)]):
    state = release_state()
    require_frozen(state, request.release_id)
    case = next((c for c in state["cases"] if c["id"] == request.case_id), None)
    if not case or request.purpose == "smoke" and not any(s["id"] == request.scene_id and s["case_id"] == request.case_id for s in SCENES):
        raise AppError(status_code=422, code="INVALID_FINAL_CASE", message="Caso ou cena não pertence ao catálogo final.")
    file = None
    if case.get("fixture"):
        file = UploadFile(io.BytesIO((RELEASE_ROOT / "fixtures" / case["fixture"]).read_bytes()), filename=case["fixture"], headers=Headers({"content-type": "application/pdf"}))
    result = await run_flow(service=service, question=case["question"], mode=case["mode"], file=file)
    final_state = release_state()
    same = final_state["frozen"] and final_state["manifest"]["release_id"] == request.release_id
    return {**result, "origin": "t6", "release_id": request.release_id if same else None, "case_id": case["id"], "expected": case["expected"], "input_file": case.get("fixture"), "purpose": request.purpose, "scene_id": request.scene_id if request.purpose == "smoke" else None, "success": None, "critical": None, "release_changed": not same}

@router.post("/package")
async def package(data: DeliveryInput):
    state = release_state()
    require_frozen(state, data.release_id)
    report = audit(data, state)
    try: content = await run_in_threadpool(build_package, data, report, state)
    except ValueError as error:
        raise AppError(status_code=409, code="PACKAGE_INVALID", message=str(error)) from error
    prefix = "entrega" if report["recorded"] else "rascunho"
    return Response(content, media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{prefix}-{state["manifest"]["release_id"]}.zip"'})

@router.post("/presentation")
async def slides(data: DeliveryInput):
    state = release_state()
    require_frozen(state, data.release_id)
    try:
        content = await run_in_threadpool(presentation, data, audit(data, state), state["manifest"])
    except ValueError as error:
        raise AppError(status_code=422, code="PRESENTATION_INVALID", message=str(error)) from error
    return Response(content, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="apresentacao.pdf"'})
