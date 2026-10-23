"""Reglas de fechas de los contratos, sin base de datos (RC-02, RC-06, D-2).

La consulta SQL equivalente del estado está en `consultas.py`; las pruebas comprueban que
las dos coinciden.
"""

import calendar
from datetime import date, timedelta
from enum import StrEnum

_UN_DIA = timedelta(days=1)


class EstadoContrato(StrEnum):
    POR_INICIAR = "por_iniciar"
    VIGENTE = "vigente"
    VENCIDO = "vencido"
    EN_TERMINACION = "en_terminacion"
    TERMINADO = "terminado"
    RENOVADO = "renovado"
    ANULADO = "anulado"


# Estados en que el apartaestudio está ocupado (RN-02).
OCUPAN = frozenset({EstadoContrato.VIGENTE, EstadoContrato.VENCIDO, EstadoContrato.EN_TERMINACION})
# Estados que admiten prórroga, renovación y terminación.
EN_CURSO = frozenset({EstadoContrato.VIGENTE, EstadoContrato.VENCIDO})


def estado(
    hoy: date,
    *,
    fecha_inicio: date,
    fecha_terminacion: date,
    fecha_entrega: date | None,
    fin_reserva: date | None,
    anulado: bool,
) -> EstadoContrato:
    """RC-02. `fin_reserva` sin `fecha_entrega` significa que el contrato fue renovado y
    termina el día anterior al inicio del contrato nuevo."""
    if anulado:
        return EstadoContrato.ANULADO
    if fecha_entrega is not None:
        if hoy > fecha_entrega:
            return EstadoContrato.TERMINADO
        return EstadoContrato.EN_TERMINACION
    if fin_reserva is not None and hoy > fin_reserva:
        return EstadoContrato.RENOVADO
    if hoy < fecha_inicio:
        return EstadoContrato.POR_INICIAR
    if hoy > fecha_terminacion:
        return EstadoContrato.VENCIDO
    return EstadoContrato.VIGENTE


def mismo_dia_en(anio: int, mes: int, dia: int) -> date:
    """RN-15: si el día no existe en ese mes, el último día del mes."""
    return date(anio, mes, min(dia, calendar.monthrange(anio, mes)[1]))


def inicio_periodo(fecha_inicio: date, numero: int) -> date:
    """Inicio del período `numero` (0 es el primero), contado desde el día de ingreso (RN-13).

    Siempre se calcula desde el día original: tras un 28 de febrero sigue el 31 de marzo."""
    meses = fecha_inicio.month - 1 + numero
    return mismo_dia_en(fecha_inicio.year + meses // 12, meses % 12 + 1, fecha_inicio.day)


def primer_inicio_de_periodo_despues(fecha_inicio: date, limite: date) -> date:
    """El primer inicio de período estrictamente posterior a `limite`."""
    meses = (limite.year - fecha_inicio.year) * 12 + limite.month - fecha_inicio.month
    numero = max(meses, 0)
    while (inicio := inicio_periodo(fecha_inicio, numero)) <= limite:
        numero += 1
    return inicio


def proximo_corte(fecha_inicio: date, hoy: date) -> date:
    """Próximo día de corte desde hoy, incluido hoy (RN-13, RN-15)."""
    if hoy <= fecha_inicio:
        return fecha_inicio
    return primer_inicio_de_periodo_despues(fecha_inicio, hoy - _UN_DIA)


def proximo_aniversario(fecha_inicio: date, hoy: date) -> date:
    """Próximo aniversario estrictamente posterior a hoy. Un 29 de febrero cae el 28 en años
    no bisiestos (RC-06)."""
    anio = max(hoy.year, fecha_inicio.year + 1)
    while (aniversario := mismo_dia_en(anio, fecha_inicio.month, fecha_inicio.day)) <= hoy:
        anio += 1
    return aniversario


def inicio_renovacion(fecha_inicio: date, fecha_terminacion: date, hoy: date) -> date:
    """D-2: el día en que empezaría el siguiente período del contrato anterior después de su
    terminación, o después de hoy si ya está vencido. Así no hay cobro doble ni hueco."""
    return primer_inicio_de_periodo_despues(fecha_inicio, max(hoy, fecha_terminacion))
