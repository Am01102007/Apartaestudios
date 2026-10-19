"""Ayudas compartidas por los servicios de propietarios y apartaestudios."""

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import ReglaDeNegocio


def guardar(sesion: Session, si_duplicado: ReglaDeNegocio) -> None:
    """flush dentro de un punto de guardado: si otra petición registró el mismo documento o
    código al mismo tiempo, la restricción única lo detiene y se informa como regla de negocio."""
    try:
        with sesion.begin_nested():
            sesion.flush()
    except IntegrityError as exc:
        raise si_duplicado from exc


def instantanea(objeto: Any, campos: tuple[str, ...]) -> dict[str, Any]:
    return {campo: getattr(objeto, campo) for campo in campos}


def cambios_de(objeto: Any, datos: dict[str, Any]) -> dict[str, Any]:
    return {campo: valor for campo, valor in datos.items() if getattr(objeto, campo) != valor}
