"""Comandos de consola: `uv run python -m app.comandos.<nombre>`."""

from sqlalchemy.orm import Session

from app.core.config import obtener_configuracion
from app.db.sesion import crear_fabrica, crear_motor


def abrir_sesion() -> Session:
    """Sesión de base de datos con la configuración del entorno (.env)."""
    return crear_fabrica(crear_motor(obtener_configuracion().database_url))()
