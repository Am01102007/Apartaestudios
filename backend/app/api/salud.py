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


class EstadoSalud(BaseModel):
    estado: str
    base_de_datos: str


@router.get("/salud", response_model=EstadoSalud, summary="Estado de la API")
def salud(sesion: Annotated[Session, Depends(obtener_sesion)]):
    try:
        sesion.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503, content={"estado": "degradado", "base_de_datos": "sin_conexion"}
        )
    return EstadoSalud(estado="ok", base_de_datos="ok")
