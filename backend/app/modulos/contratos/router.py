"""Contratos: /contratos/*, más /apartaestudios/{id}/contratos y /residentes/{id}/contratos.

Ambos roles crean, prorrogan, renuevan y terminan; solo el administrador anula. El estado se
calcula en cada respuesta con la fecha de hoy en Bogotá (RC-01).
"""

from fastapi import APIRouter, Depends

from app.api.dependencias import BD, IP, Reloj
from app.core.tiempo import hoy
from app.modulos.contratos import servicio
from app.modulos.contratos.esquemas import (
    Anulacion,
    Cambio,
    ContratoCrear,
    ContratoDetalle,
    ContratoEditar,
    ContratoSalida,
    ProrrogaCrear,
    RenovacionCrear,
    TerminacionCrear,
)
from app.modulos.contratos.estados import EstadoContrato
from app.modulos.usuarios.dependencias import SesionActual, SesionAdministrador, requiere_sesion

router = APIRouter(prefix="/contratos", tags=["contratos"], dependencies=[Depends(requiere_sesion)])
router_relacionados = APIRouter(tags=["contratos"], dependencies=[Depends(requiere_sesion)])


@router.get("", response_model=list[ContratoSalida], summary="Listar contratos")
def listar(
    bd: BD,
    reloj: Reloj,
    estado: EstadoContrato | None = None,
    propietario_id: int | None = None,
    apartaestudio_id: int | None = None,
    residente_id: int | None = None,
):
    return servicio.listar(
        bd,
        hoy=hoy(reloj()),
        estado=estado,
        propietario_id=propietario_id,
        apartaestudio_id=apartaestudio_id,
        residente_id=residente_id,
    )


@router.post("", response_model=ContratoDetalle, status_code=201, summary="Crear contrato")
def crear(datos: ContratoCrear, actual: SesionActual, bd: BD, ip: IP, reloj: Reloj):
    contrato = servicio.crear(bd, datos, actor_id=actual.usuario_id, ip=ip, hoy=hoy(reloj()))
    bd.commit()
    return contrato


@router.get("/{contrato_id}", response_model=ContratoDetalle, summary="Detalle de un contrato")
def detalle(contrato_id: int, bd: BD, reloj: Reloj):
    return servicio.obtener(bd, contrato_id, hoy=hoy(reloj()))


@router.patch(
    "/{contrato_id}", response_model=ContratoDetalle, summary="Editar contrato sin cobros"
)
def editar(
    contrato_id: int, datos: ContratoEditar, actual: SesionActual, bd: BD, ip: IP, reloj: Reloj
):
    contrato = servicio.editar(
        bd, contrato_id, datos, actor_id=actual.usuario_id, ip=ip, hoy=hoy(reloj())
    )
    bd.commit()
    return contrato


@router.post(
    "/{contrato_id}/prorrogar", response_model=ContratoDetalle, summary="Prorrogar contrato"
)
def prorrogar(
    contrato_id: int, datos: ProrrogaCrear, actual: SesionActual, bd: BD, ip: IP, reloj: Reloj
):
    ahora = reloj()
    contrato = servicio.prorrogar(
        bd,
        contrato_id,
        datos.fecha_terminacion,
        actor_id=actual.usuario_id,
        ip=ip,
        ahora=ahora,
        hoy=hoy(ahora),
    )
    bd.commit()
    return contrato


@router.post(
    "/{contrato_id}/renovar",
    response_model=ContratoDetalle,
    status_code=201,
    summary="Renovar: cierra el contrato y crea uno nuevo enlazado",
)
def renovar(
    contrato_id: int, datos: RenovacionCrear, actual: SesionActual, bd: BD, ip: IP, reloj: Reloj
):
    contrato = servicio.renovar(
        bd, contrato_id, datos, actor_id=actual.usuario_id, ip=ip, hoy=hoy(reloj())
    )
    bd.commit()
    return contrato


@router.post(
    "/{contrato_id}/terminar",
    response_model=ContratoDetalle,
    summary="Registrar o corregir aviso, entrega y motivo de terminación",
)
def terminar(
    contrato_id: int, datos: TerminacionCrear, actual: SesionActual, bd: BD, ip: IP, reloj: Reloj
):
    contrato = servicio.terminar(
        bd, contrato_id, datos, actor_id=actual.usuario_id, ip=ip, hoy=hoy(reloj())
    )
    bd.commit()
    return contrato


@router.post(
    "/{contrato_id}/anular",
    response_model=ContratoDetalle,
    summary="Anular un contrato por iniciar",
)
def anular(
    contrato_id: int, datos: Anulacion, actual: SesionAdministrador, bd: BD, ip: IP, reloj: Reloj
):
    ahora = reloj()
    contrato = servicio.anular(
        bd,
        contrato_id,
        datos.motivo,
        actor_id=actual.usuario_id,
        ip=ip,
        ahora=ahora,
        hoy=hoy(ahora),
    )
    bd.commit()
    return contrato


@router.get(
    "/{contrato_id}/historial",
    response_model=list[Cambio],
    summary="Cambios del contrato con autor y fecha",
)
def historial(contrato_id: int, bd: BD):
    return [
        Cambio(
            momento=registro.momento,
            accion=registro.accion,
            usuario=registro.usuario,
            valor_anterior=registro.valor_anterior,
            valor_nuevo=registro.valor_nuevo,
        )
        for registro in servicio.historial(bd, contrato_id)
    ]


@router_relacionados.get(
    "/apartaestudios/{apartaestudio_id}/contratos",
    response_model=list[ContratoSalida],
    summary="Contratos de un apartaestudio",
)
def de_apartaestudio(apartaestudio_id: int, bd: BD, reloj: Reloj):
    return servicio.de_apartaestudio(bd, apartaestudio_id, hoy=hoy(reloj()))


@router_relacionados.get(
    "/residentes/{residente_id}/contratos",
    response_model=list[ContratoSalida],
    summary="Contratos de un residente",
)
def de_residente(residente_id: int, bd: BD, reloj: Reloj):
    return servicio.de_residente(bd, residente_id, hoy=hoy(reloj()))
