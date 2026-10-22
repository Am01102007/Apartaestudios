"""Residentes: /residentes/*. Consultan ambos roles; modifica solo el administrador."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencias import BD, IP
from app.modulos.bloqueos import servicio as bloqueos
from app.modulos.residentes import servicio
from app.modulos.residentes.esquemas import (
    ResidenteCrear,
    ResidenteDetalle,
    ResidenteEditar,
    ResidenteSalida,
)
from app.modulos.usuarios.dependencias import SesionActual, SesionAdministrador, requiere_sesion

router = APIRouter(
    prefix="/residentes", tags=["residentes"], dependencies=[Depends(requiere_sesion)]
)


@router.get("", response_model=list[ResidenteSalida], summary="Directorio de residentes")
def listar(
    bd: BD,
    texto: Annotated[
        str | None, Query(max_length=100, description="Busca en el nombre y el documento")
    ] = None,
):
    return servicio.listar(bd, texto=texto)


@router.post("", response_model=ResidenteSalida, status_code=201, summary="Registrar residente")
def crear(datos: ResidenteCrear, actual: SesionAdministrador, bd: BD, ip: IP):
    residente = servicio.crear(bd, datos, actor_id=actual.usuario_id, ip=ip)
    bd.commit()
    return residente


@router.get(
    "/{residente_id}",
    response_model=ResidenteDetalle,
    summary="Detalle de un residente con su bloqueo activo",
)
def detalle(residente_id: int, actual: SesionActual, bd: BD):
    residente, bloqueo = servicio.detalle(bd, residente_id)
    salida_bloqueo = (
        None
        if bloqueo is None
        else bloqueos.salida(bloqueo, ve_motivos=actual.usuario.es_administrador)
    )
    return ResidenteDetalle.construir(residente, salida_bloqueo)


@router.patch("/{residente_id}", response_model=ResidenteSalida, summary="Editar residente")
def editar(residente_id: int, datos: ResidenteEditar, actual: SesionAdministrador, bd: BD, ip: IP):
    residente = servicio.editar(bd, residente_id, datos, actor_id=actual.usuario_id, ip=ip)
    bd.commit()
    return residente
