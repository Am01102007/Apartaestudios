"""Fechas de negocio en la zona horaria de Bogotá (RNF-10).

Todo cálculo de cortes, vencimientos y mora debe usar `hoy()` y no `date.today()`, que
depende de la zona horaria del servidor.
"""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

ZONA_NEGOCIO = ZoneInfo("America/Bogota")


def ahora_utc() -> datetime:
    """Momento actual en UTC, para columnas TIMESTAMPTZ."""
    return datetime.now(UTC)


def hoy(momento: datetime | None = None) -> date:
    """Fecha de negocio (día en Bogotá) del momento dado, o de ahora."""
    momento = momento or ahora_utc()
    if momento.tzinfo is None:
        raise ValueError("El momento debe incluir zona horaria")
    return momento.astimezone(ZONA_NEGOCIO).date()
