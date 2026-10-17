from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from app.core.tiempo import hoy


def test_hoy_usa_el_dia_de_bogota_y_no_el_de_utc():
    # 04:30 UTC del 17 de octubre son las 23:30 del 16 de octubre en Bogotá (UTC-5).
    assert hoy(datetime(2026, 10, 17, 4, 30, tzinfo=UTC)) == date(2026, 10, 16)


def test_hoy_cambia_de_dia_a_medianoche_de_bogota():
    assert hoy(datetime(2026, 10, 17, 5, 0, tzinfo=UTC)) == date(2026, 10, 17)


def test_hoy_convierte_desde_cualquier_zona():
    madrid = timezone(timedelta(hours=2))
    assert hoy(datetime(2026, 10, 17, 6, 0, tzinfo=madrid)) == date(2026, 10, 16)


def test_hoy_rechaza_momentos_sin_zona_horaria():
    with pytest.raises(ValueError):
        hoy(datetime(2026, 10, 17, 12, 0))
