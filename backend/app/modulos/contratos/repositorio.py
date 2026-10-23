from datetime import date

from sqlalchemy import Row, select
from sqlalchemy.orm import Session, aliased

from app.modulos.contratos import consultas
from app.modulos.contratos.estados import EstadoContrato
from app.modulos.contratos.modelos import Contrato, Prorroga
from app.modulos.inmuebles.modelos import Apartaestudio


def _siguiente():
    """Renovación vigente (no anulada) de cada contrato, para enlazarla en la salida."""
    siguiente = aliased(Contrato)
    return (
        select(siguiente.id)
        .where(siguiente.contrato_anterior_id == Contrato.id, siguiente.anulado_en.is_(None))
        .scalar_subquery()
    )


def _con_calculados(hoy: date):
    return select(
        Contrato, consultas.estado(hoy).label("estado"), _siguiente().label("siguiente_id")
    )


def obtener(sesion: Session, contrato_id: int, *, bloquear: bool = False) -> Contrato | None:
    consulta = select(Contrato).where(Contrato.id == contrato_id)
    if bloquear:
        consulta = consulta.with_for_update(of=Contrato).execution_options(populate_existing=True)
    return sesion.scalar(consulta)


def calculados(sesion: Session, contrato_id: int, hoy: date) -> Row | None:
    return sesion.execute(_con_calculados(hoy).where(Contrato.id == contrato_id)).one_or_none()


def listar(
    sesion: Session,
    *,
    hoy: date,
    estado: EstadoContrato | None = None,
    propietario_id: int | None = None,
    apartaestudio_id: int | None = None,
    residente_id: int | None = None,
) -> list[Row]:
    consulta = _con_calculados(hoy).order_by(Contrato.fecha_inicio.desc(), Contrato.id.desc())
    if estado is not None:
        consulta = consulta.where(consultas.estado(hoy) == estado.value)
    if propietario_id is not None:
        consulta = consulta.join(Contrato.apartaestudio).where(
            Apartaestudio.propietario_id == propietario_id
        )
    if apartaestudio_id is not None:
        consulta = consulta.where(Contrato.apartaestudio_id == apartaestudio_id)
    if residente_id is not None:
        consulta = consulta.where(Contrato.residente_id == residente_id)
    return list(sesion.execute(consulta))


def apartaestudio_reservado(sesion: Session, apartaestudio_id: int, hoy: date) -> bool:
    """RN-04: tiene un contrato por iniciar, vigente, vencido o en terminación."""
    return bool(sesion.scalar(select(consultas.apartaestudio_reservado(apartaestudio_id, hoy))))


def renovacion_de(sesion: Session, contrato_id: int) -> Contrato | None:
    return sesion.scalar(
        select(Contrato).where(
            Contrato.contrato_anterior_id == contrato_id, Contrato.anulado_en.is_(None)
        )
    )


def prorrogas(sesion: Session, contrato_id: int) -> list[Prorroga]:
    return list(
        sesion.scalars(
            select(Prorroga)
            .where(Prorroga.contrato_id == contrato_id)
            .order_by(Prorroga.registrada_en, Prorroga.id)
        )
    )
