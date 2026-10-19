"""Propietarios: /propietarios/*. Consultan ambos roles; modifica solo el administrador.

Cada endpoint que modifica confirma la transacción con `bd.commit()` cuando el servicio
termina sin error.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencias import BD, IP, Reloj
from app.core.tiempo import hoy
from app.modulos.inmuebles import propietarios as servicio
from app.modulos.inmuebles.esquemas import (
    PropietarioCrear,
    PropietarioDetalle,
    PropietarioEditar,
    PropietarioSalida,
)
from app.modulos.usuarios.dependencias import SesionAdministrador, requiere_sesion

router = APIRouter(
    prefix="/propietarios", tags=["propietarios"], dependencies=[Depends(requiere_sesion)]
)


@router.get("", response_model=list[PropietarioSalida], summary="Listar propietarios")
def listar(
    bd: BD,
    activo: bool | None = None,
    texto: Annotated[
        str | None, Query(max_length=100, description="Busca en el nombre y el documento")
    ] = None,
):
    return servicio.listar(bd, activo=activo, texto=texto)


@router.post("", response_model=PropietarioSalida, status_code=201, summary="Crear propietario")
def crear(datos: PropietarioCrear, actual: SesionAdministrador, bd: BD, ip: IP):
    propietario = servicio.crear(bd, datos, actor_id=actual.usuario_id, ip=ip)
    bd.commit()
    return propietario


@router.get(
    "/{propietario_id}",
    response_model=PropietarioDetalle,
    summary="Detalle de un propietario con sus apartaestudios",
)
def detalle(propietario_id: int, bd: BD, reloj: Reloj):
    return servicio.detalle(bd, propietario_id, hoy=hoy(reloj()))


@router.patch("/{propietario_id}", response_model=PropietarioSalida, summary="Editar propietario")
def editar(
    propietario_id: int, datos: PropietarioEditar, actual: SesionAdministrador, bd: BD, ip: IP
):
    propietario = servicio.editar(bd, propietario_id, datos, actor_id=actual.usuario_id, ip=ip)
    bd.commit()
    return propietario


@router.post(
    "/{propietario_id}/desactivar",
    response_model=PropietarioSalida,
    summary="Desactivar propietario (sin apartaestudios activos)",
)
def desactivar(propietario_id: int, actual: SesionAdministrador, bd: BD, ip: IP):
    propietario = servicio.desactivar(bd, propietario_id, actor_id=actual.usuario_id, ip=ip)
    bd.commit()
    return propietario


@router.post(
    "/{propietario_id}/activar", response_model=PropietarioSalida, summary="Activar propietario"
)
def activar(propietario_id: int, actual: SesionAdministrador, bd: BD, ip: IP):
    propietario = servicio.activar(bd, propietario_id, actor_id=actual.usuario_id, ip=ip)
    bd.commit()
    return propietario
