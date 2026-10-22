"""Bloqueos: /bloqueos/*. Consultan ambos roles; bloquea y levanta solo el administrador.

Los motivos solo se muestran al administrador (D-3).
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencias import BD, IP, Reloj
from app.core.documentos import TipoDocumento
from app.core.entradas import NumeroDocumento
from app.modulos.bloqueos import servicio
from app.modulos.bloqueos.esquemas import BloqueoCrear, BloqueoSalida, Levantamiento, Verificacion
from app.modulos.bloqueos.modelos import EstadoBloqueo
from app.modulos.usuarios.dependencias import SesionActual, SesionAdministrador

router = APIRouter(prefix="/bloqueos", tags=["bloqueos"])


@router.get("", response_model=list[BloqueoSalida], summary="Listar bloqueos")
def listar(
    actual: SesionActual,
    bd: BD,
    estado: EstadoBloqueo = EstadoBloqueo.ACTIVOS,
    texto: Annotated[
        str | None, Query(max_length=100, description="Busca en el nombre y el documento")
    ] = None,
):
    ve_motivos = actual.usuario.es_administrador
    return [
        servicio.salida(b, ve_motivos=ve_motivos)
        for b in servicio.listar(bd, estado=estado, texto=texto)
    ]


@router.get(
    "/verificar",
    response_model=Verificacion,
    summary="Indica si un documento tiene bloqueo activo",
)
def verificar(
    _: SesionActual,
    bd: BD,
    tipo_documento: TipoDocumento,
    numero_documento: Annotated[NumeroDocumento, Query()],
):
    bloqueo = servicio.bloqueo_activo(bd, tipo_documento, numero_documento)
    if bloqueo is None:
        return Verificacion(bloqueado=False)
    return Verificacion(bloqueado=True, bloqueo_id=bloqueo.id, desde=bloqueo.bloqueado_en)


@router.post("", response_model=BloqueoSalida, status_code=201, summary="Bloquear una persona")
def bloquear(datos: BloqueoCrear, actual: SesionAdministrador, bd: BD, ip: IP, reloj: Reloj):
    bloqueo = servicio.bloquear(bd, datos, actor_id=actual.usuario_id, ip=ip, ahora=reloj())
    bd.commit()
    return servicio.salida(bloqueo, ve_motivos=True)


@router.post("/{bloqueo_id}/levantar", response_model=BloqueoSalida, summary="Levantar un bloqueo")
def levantar(
    bloqueo_id: int,
    datos: Levantamiento,
    actual: SesionAdministrador,
    bd: BD,
    ip: IP,
    reloj: Reloj,
):
    bloqueo = servicio.levantar(
        bd, bloqueo_id, datos.motivo, actor_id=actual.usuario_id, ip=ip, ahora=reloj()
    )
    bd.commit()
    return servicio.salida(bloqueo, ve_motivos=True)
