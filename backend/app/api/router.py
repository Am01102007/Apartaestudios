"""Agrupa los routers de todos los dominios bajo /api/v1."""

from fastapi import APIRouter

from app.api import salud
from app.modulos.auditoria.router import router as auditoria
from app.modulos.bloqueos.router import router as bloqueos
from app.modulos.contratos.router import router as contratos
from app.modulos.contratos.router import router_relacionados as contratos_relacionados
from app.modulos.inmuebles.router_apartaestudios import router as apartaestudios
from app.modulos.inmuebles.router_propietarios import router as propietarios
from app.modulos.residentes.router import router as residentes
from app.modulos.usuarios.router import router as usuarios
from app.modulos.usuarios.router_auth import router as auth

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(salud.router)
api_v1.include_router(auth)
api_v1.include_router(usuarios)
api_v1.include_router(propietarios)
api_v1.include_router(apartaestudios)
api_v1.include_router(residentes)
api_v1.include_router(bloqueos)
api_v1.include_router(contratos)
api_v1.include_router(contratos_relacionados)
api_v1.include_router(auditoria)
