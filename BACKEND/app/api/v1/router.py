"""Agregador das rotas da API v1."""

from fastapi import APIRouter

from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.documents import router as documents_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.t4 import router as t4_router
from app.api.v1.routes.t5 import router as t5_router
from app.api.v1.routes.t6 import router as t6_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(documents_router)
api_router.include_router(t4_router)
api_router.include_router(t5_router)
api_router.include_router(t6_router)
