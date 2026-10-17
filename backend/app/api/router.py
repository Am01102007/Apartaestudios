"""Agrupa los routers de todos los dominios bajo /api/v1."""

from fastapi import APIRouter

from app.api import salud
from app.modulos.auditoria.router import router as auditoria
from app.modulos.usuarios.router import router as usuarios
from app.modulos.usuarios.router_auth import router as auth

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(salud.router)
api_v1.include_router(auth)
api_v1.include_router(usuarios)
api_v1.include_router(auditoria)
