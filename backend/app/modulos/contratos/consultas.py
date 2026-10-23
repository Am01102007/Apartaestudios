"""Expresiones SQL del estado y la ocupación, equivalentes a `estados.py` (RC-01 a RC-03).

Las usa también el módulo de inmuebles para calcular la ocupación en sus consultas.
"""

from datetime import date

from sqlalchemy import ColumnElement, and_, case, exists, literal, or_

from app.modulos.contratos.estados import EstadoContrato
from app.modulos.contratos.modelos import Contrato


def estado(hoy: date) -> ColumnElement[str]:
    dia = literal(hoy)
    return case(
        (Contrato.anulado_en.is_not(None), EstadoContrato.ANULADO.value),
        (
            Contrato.fecha_entrega.is_not(None),
            case(
                (dia > Contrato.fecha_entrega, EstadoContrato.TERMINADO.value),
                else_=EstadoContrato.EN_TERMINACION.value,
            ),
        ),
        (
            and_(Contrato.fin_reserva.is_not(None), dia > Contrato.fin_reserva),
            EstadoContrato.RENOVADO.value,
        ),
        (dia < Contrato.fecha_inicio, EstadoContrato.POR_INICIAR.value),
        (dia > Contrato.fecha_terminacion, EstadoContrato.VENCIDO.value),
        else_=EstadoContrato.VIGENTE.value,
    )


def ocupa(hoy: date) -> ColumnElement[bool]:
    """El contrato ocupa hoy su apartaestudio: vigente, vencido o en terminación."""
    return and_(
        Contrato.anulado_en.is_(None),
        Contrato.fecha_inicio <= hoy,
        or_(Contrato.fin_reserva.is_(None), Contrato.fin_reserva >= hoy),
    )


def reserva_desde(hoy: date) -> ColumnElement[bool]:
    """El contrato reserva su apartaestudio hoy o más adelante: por iniciar, vigente, vencido
    o en terminación (RN-04, C-16)."""
    return and_(
        Contrato.anulado_en.is_(None),
        or_(Contrato.fin_reserva.is_(None), Contrato.fin_reserva >= hoy),
    )


def apartaestudio_ocupado(apartaestudio_id, hoy: date) -> ColumnElement[bool]:
    """EXISTS para usar en consultas de apartaestudios (RC-03)."""
    return exists().where(Contrato.apartaestudio_id == apartaestudio_id, ocupa(hoy))


def apartaestudio_reservado(apartaestudio_id, hoy: date) -> ColumnElement[bool]:
    return exists().where(Contrato.apartaestudio_id == apartaestudio_id, reserva_desde(hoy))
