"""Conexión a PostgreSQL y sesión por petición.

Regla de transacciones: el servicio que ejecuta un caso de uso decide cuándo confirmar
(`with sesion.begin():`). Si el caso de uso lanza una excepción, todo se revierte; así una
operación financiera nunca queda a medias (RNF-06).
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import obtener_configuracion


def crear_motor(url: str) -> Engine:
    # La conexión trabaja en UTC; las fechas de negocio se calculan en app.core.tiempo.
    return create_engine(url, pool_pre_ping=True, connect_args={"options": "-c timezone=UTC"})


motor = crear_motor(obtener_configuracion().database_url)
FabricaSesiones = sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def obtener_sesion() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por petición, cerrada siempre al final."""
    sesion = FabricaSesiones()
    try:
        yield sesion
    finally:
        sesion.close()
