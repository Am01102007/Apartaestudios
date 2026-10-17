"""Conexión a PostgreSQL y sesión por petición.

Regla de transacciones (unidad de trabajo, RNF-06): los servicios nunca confirman; solo
modifican y, si lo necesitan, hacen `flush()`. El punto de entrada del caso de uso (el
endpoint o el comando de consola) confirma una sola vez con `bd.commit()` al final. Si algo
falla antes, la sesión se cierra sin confirmar y PostgreSQL revierte todo, aunque el caso de
uso haya pasado por servicios de varios dominios.
"""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def crear_motor(url: str) -> Engine:
    # La conexión trabaja en UTC; las fechas de negocio se calculan en app.core.tiempo.
    return create_engine(url, pool_pre_ping=True, connect_args={"options": "-c timezone=UTC"})


def crear_fabrica(motor: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=motor, autoflush=False, expire_on_commit=False)


def obtener_sesion(request: Request) -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por petición, cerrada siempre al final."""
    sesion = request.app.state.fabrica_sesiones()
    try:
        yield sesion
    finally:
        sesion.close()
