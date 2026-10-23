"""Reglas de fechas de los contratos (RC-02, RC-06, RN-13, RN-15, D-2), sin base de datos."""

from datetime import date

import pytest

from app.modulos.contratos.estados import (
    EstadoContrato as E,
)
from app.modulos.contratos.estados import (
    estado,
    inicio_periodo,
    inicio_renovacion,
    proximo_aniversario,
    proximo_corte,
)

INICIO, FIN = date(2026, 1, 14), date(2027, 1, 13)


def _estado(hoy, entrega=None, fin_reserva=None, anulado=False):
    return estado(
        hoy,
        fecha_inicio=INICIO,
        fecha_terminacion=FIN,
        fecha_entrega=entrega,
        fin_reserva=fin_reserva,
        anulado=anulado,
    )


@pytest.mark.parametrize(
    ("hoy", "esperado"),
    [
        (date(2026, 1, 13), E.POR_INICIAR),
        (date(2026, 1, 14), E.VIGENTE),
        (date(2027, 1, 13), E.VIGENTE),
        (date(2027, 1, 14), E.VENCIDO),
    ],
)
def test_por_iniciar_vigente_y_vencido_en_sus_dias_limite(hoy, esperado):
    assert _estado(hoy) == esperado


def test_en_terminacion_hasta_la_entrega_y_terminado_desde_el_dia_siguiente():
    entrega = date(2026, 6, 30)
    assert _estado(date(2026, 6, 1), entrega, entrega) == E.EN_TERMINACION
    assert _estado(entrega, entrega, entrega) == E.EN_TERMINACION
    assert _estado(date(2026, 7, 1), entrega, entrega) == E.TERMINADO


def test_entrega_posterior_a_la_terminacion_sigue_en_terminacion():
    entrega = date(2027, 2, 20)
    assert _estado(date(2027, 2, 1), entrega, entrega) == E.EN_TERMINACION


def test_renovado_desde_el_inicio_del_contrato_nuevo():
    fin_reserva = date(2027, 1, 13)
    assert _estado(date(2027, 1, 13), fin_reserva=fin_reserva) == E.VIGENTE
    assert _estado(date(2027, 1, 14), fin_reserva=fin_reserva) == E.RENOVADO


def test_renovacion_registrada_despues_de_vencer_sigue_vencido_hasta_el_cambio():
    fin_reserva = date(2027, 3, 13)
    assert _estado(date(2027, 2, 20), fin_reserva=fin_reserva) == E.VENCIDO
    assert _estado(date(2027, 3, 14), fin_reserva=fin_reserva) == E.RENOVADO


def test_anulado_tiene_prioridad():
    assert _estado(date(2026, 1, 1), anulado=True) == E.ANULADO


@pytest.mark.parametrize(
    ("inicio", "numero", "esperado"),
    [
        (date(2026, 1, 31), 1, date(2026, 2, 28)),  # CA-05
        (date(2026, 1, 31), 2, date(2026, 3, 31)),
        (date(2026, 1, 31), 3, date(2026, 4, 30)),
        (date(2028, 1, 31), 1, date(2028, 2, 29)),  # bisiesto
        (date(2026, 1, 30), 1, date(2026, 2, 28)),
        (date(2026, 1, 29), 1, date(2026, 2, 28)),
        (date(2026, 1, 14), 12, date(2027, 1, 14)),
        (date(2026, 11, 30), 3, date(2027, 2, 28)),
    ],
)
def test_inicios_de_periodo_en_dias_29_30_y_31(inicio, numero, esperado):
    assert inicio_periodo(inicio, numero) == esperado


@pytest.mark.parametrize(
    ("hoy", "esperado"),
    [
        (date(2026, 1, 1), date(2026, 1, 31)),
        (date(2026, 1, 31), date(2026, 1, 31)),
        (date(2026, 2, 1), date(2026, 2, 28)),
        (date(2026, 2, 28), date(2026, 2, 28)),
        (date(2026, 3, 1), date(2026, 3, 31)),
    ],
)
def test_proximo_corte_incluye_hoy(hoy, esperado):
    assert proximo_corte(date(2026, 1, 31), hoy) == esperado


@pytest.mark.parametrize(
    ("inicio", "hoy", "esperado"),
    [
        (date(2026, 1, 14), date(2026, 1, 14), date(2027, 1, 14)),
        (date(2026, 1, 14), date(2027, 1, 14), date(2028, 1, 14)),
        (date(2028, 2, 29), date(2028, 3, 1), date(2029, 2, 28)),
        (date(2028, 2, 29), date(2031, 6, 1), date(2032, 2, 29)),
        (date(2026, 10, 20), date(2026, 10, 17), date(2027, 10, 20)),
    ],
)
def test_proximo_aniversario(inicio, hoy, esperado):
    assert proximo_aniversario(inicio, hoy) == esperado


@pytest.mark.parametrize(
    ("inicio", "fin", "hoy", "esperado"),
    [
        # Ejemplo de D-2: del 14 de enero al 13 de enero, la renovación empieza el 14.
        (date(2026, 1, 14), date(2027, 1, 13), date(2026, 12, 1), date(2027, 1, 14)),
        # Terminación que no coincide con un período: el último período ya cubre hasta el 13.
        (date(2026, 1, 14), date(2026, 12, 31), date(2026, 12, 1), date(2027, 1, 14)),
        # Ya vencido: el siguiente período después de hoy.
        (date(2026, 1, 14), date(2027, 1, 13), date(2027, 3, 2), date(2027, 3, 14)),
        # Vencido y hoy es día de corte: ese período ya es del contrato anterior.
        (date(2026, 1, 14), date(2027, 1, 13), date(2027, 3, 14), date(2027, 4, 14)),
        # Día 31 con meses cortos.
        (date(2026, 1, 31), date(2027, 1, 30), date(2026, 6, 1), date(2027, 1, 31)),
        (date(2026, 1, 31), date(2026, 2, 27), date(2026, 2, 1), date(2026, 2, 28)),
    ],
)
def test_inicio_de_la_renovacion(inicio, fin, hoy, esperado):
    assert inicio_renovacion(inicio, fin, hoy) == esperado
