"""Agrupa los routers de todos los dominios bajo /api/v1.

Cada módulo de la fase 8 añade aquí su router, por ejemplo:
    from app.modulos.usuarios.router import router as usuarios
    api_v1.include_router(usuarios)
"""

from fastapi import APIRouter

from app.api import salud

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(salud.router)
