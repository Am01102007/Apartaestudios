"""Dependencias comunes de FastAPI que no pertenecen a un dominio."""

from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Configuracion
from app.core.tiempo import ahora_utc
from app.db.sesion import obtener_sesion


def obtener_config(request: Request) -> Configuracion:
    return request.app.state.configuracion


def obtener_reloj() -> Callable[[], datetime]:
    """Reloj de la aplicación; las pruebas lo reemplazan para simular el paso del tiempo."""
    return ahora_utc


def ip_cliente(request: Request) -> str | None:
    return request.client.host if request.client else None


BD = Annotated[Session, Depends(obtener_sesion)]
Config = Annotated[Configuracion, Depends(obtener_config)]
Reloj = Annotated[Callable[[], datetime], Depends(obtener_reloj)]
IP = Annotated[str | None, Depends(ip_cliente)]
