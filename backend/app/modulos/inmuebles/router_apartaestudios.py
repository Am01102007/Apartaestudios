"""Apartaestudios: /apartaestudios/*. Consultan ambos roles; modifica solo el administrador.

La ocupación (Libre u Ocupado) se calcula en cada respuesta y no se puede enviar (RN-02).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencias import BD, IP, Reloj
from app.core.tiempo import hoy
from app.modulos.inmuebles import apartaestudios as servicio
from app.modulos.inmuebles.esquemas import (
    ApartaestudioCrear,
    ApartaestudioEditar,
    ApartaestudioSalida,
    CambioMantenimiento,
)
from app.modulos.inmuebles.modelos import Ocupacion
from app.modulos.usuarios.dependencias import SesionAdministrador, requiere_sesion

router = APIRouter(
    prefix="/apartaestudios", tags=["apartaestudios"], dependencies=[Depends(requiere_sesion)]
)


@router.get("", response_model=list[ApartaestudioSalida], summary="Listar apartaestudios")
def listar(
    bd: BD,
    reloj: Reloj,
    propietario_id: int | None = None,
    ocupacion: Ocupacion | None = None,
    en_mantenimiento: bool | None = None,
    activo: bool | None = None,
    texto: Annotated[
        str | None, Query(max_length=100, description="Busca en el código y la dirección")
    ] = None,
):
    return servicio.listar(
        bd,
        hoy=hoy(reloj()),
        propietario_id=propietario_id,
        ocupacion=ocupacion,
        en_mantenimiento=en_mantenimiento,
        activo=activo,
        texto=texto,
    )


@router.post("", response_model=ApartaestudioSalida, status_code=201, summary="Crear apartaestudio")
def crear(datos: ApartaestudioCrear, actual: SesionAdministrador, bd: BD, ip: IP, reloj: Reloj):
    apartaestudio = servicio.crear(bd, datos, actor_id=actual.usuario_id, ip=ip, hoy=hoy(reloj()))
    bd.commit()
    return apartaestudio


@router.get(
    "/{apartaestudio_id}",
    response_model=ApartaestudioSalida,
    summary="Detalle de un apartaestudio con su ocupación",
)
def detalle(apartaestudio_id: int, bd: BD, reloj: Reloj):
    return servicio.obtener(bd, apartaestudio_id, hoy=hoy(reloj()))


@router.patch(
    "/{apartaestudio_id}", response_model=ApartaestudioSalida, summary="Editar apartaestudio"
)
def editar(
    apartaestudio_id: int,
    datos: ApartaestudioEditar,
    actual: SesionAdministrador,
    bd: BD,
    ip: IP,
    reloj: Reloj,
):
    apartaestudio = servicio.editar(
        bd, apartaestudio_id, datos, actor_id=actual.usuario_id, ip=ip, hoy=hoy(reloj())
    )
    bd.commit()
    return apartaestudio


@router.post(
    "/{apartaestudio_id}/mantenimiento",
    response_model=ApartaestudioSalida,
    summary="Activar o retirar la marca de mantenimiento",
)
def mantenimiento(
    apartaestudio_id: int,
    datos: CambioMantenimiento,
    actual: SesionAdministrador,
    bd: BD,
    ip: IP,
    reloj: Reloj,
):
    ahora = reloj()
    apartaestudio = servicio.cambiar_mantenimiento(
        bd,
        apartaestudio_id,
        activo=datos.activo,
        motivo=datos.motivo,
        actor_id=actual.usuario_id,
        ip=ip,
        ahora=ahora,
        hoy=hoy(ahora),
    )
    bd.commit()
    return apartaestudio


@router.post(
    "/{apartaestudio_id}/desactivar",
    response_model=ApartaestudioSalida,
    summary="Desactivar apartaestudio",
)
def desactivar(apartaestudio_id: int, actual: SesionAdministrador, bd: BD, ip: IP, reloj: Reloj):
    apartaestudio = servicio.desactivar(
        bd, apartaestudio_id, actor_id=actual.usuario_id, ip=ip, hoy=hoy(reloj())
    )
    bd.commit()
    return apartaestudio


@router.post(
    "/{apartaestudio_id}/activar",
    response_model=ApartaestudioSalida,
    summary="Activar apartaestudio (su propietario debe estar activo)",
)
def activar(apartaestudio_id: int, actual: SesionAdministrador, bd: BD, ip: IP, reloj: Reloj):
    apartaestudio = servicio.activar(
        bd, apartaestudio_id, actor_id=actual.usuario_id, ip=ip, hoy=hoy(reloj())
    )
    bd.commit()
    return apartaestudio
