"""Verificación de salud: indica si la API está activa y si llega a la base de datos."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.sesion import obtener_sesion

router = APIRouter(tags=["salud"])
# Rutas sin prefijo para el healthcheck de Docker Compose y Railway.
router_despliegue = APIRouter(prefix="/health", tags=["salud"])


class EstadoSalud(BaseModel):
    estado: str
    base_de_datos: str


def _base_disponible(sesion: Session) -> bool:
    try:
        sesion.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False
    return True


@router.get("/salud", response_model=EstadoSalud, summary="Estado de la API")
def salud(sesion: Annotated[Session, Depends(obtener_sesion)]):
    if not _base_disponible(sesion):
        return JSONResponse(
            status_code=503, content={"estado": "degradado", "base_de_datos": "sin_conexion"}
        )
    return EstadoSalud(estado="ok", base_de_datos="ok")


@router_despliegue.get("/live", summary="El proceso de la API responde")
def vivo() -> dict[str, str]:
    return {"status": "alive"}


@router_despliegue.get("/ready", summary="La API llega a PostgreSQL")
def listo(sesion: Annotated[Session, Depends(obtener_sesion)]):
    if not _base_disponible(sesion):
        return JSONResponse(status_code=503, content={"database": "unavailable"})
    return {"database": "ready"}
