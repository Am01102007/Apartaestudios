"""Consulta del registro de auditoría: /auditoria (solo administrador)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencias import BD
from app.modulos.auditoria import servicio
from app.modulos.auditoria.esquemas import PaginaAuditoria
from app.modulos.usuarios.dependencias import solo_administrador

router = APIRouter(
    prefix="/auditoria",
    tags=["auditoría"],
    dependencies=[Depends(solo_administrador)],
)


@router.get("", response_model=PaginaAuditoria, summary="Consultar el registro de auditoría")
def consultar(
    bd: BD,
    usuario_id: int | None = None,
    accion: str | None = None,
    entidad: str | None = None,
    entidad_id: str | None = None,
    desde: Annotated[date | None, Query(description="Día inicial, hora de Bogotá")] = None,
    hasta: Annotated[date | None, Query(description="Día final incluido, hora de Bogotá")] = None,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    desplazamiento: Annotated[int, Query(ge=0)] = 0,
):
    registros, total = servicio.consultar(
        bd,
        usuario_id=usuario_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        desde=desde,
        hasta=hasta,
        limite=limite,
        desplazamiento=desplazamiento,
    )
    return PaginaAuditoria(total=total, registros=registros)
