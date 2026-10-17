"""Registro y consulta de la auditoría (RF-23).

`registrar` añade el registro a la transacción en curso: si la operación auditada se
revierte, su registro también, y nunca queda una operación sin su rastro.
"""

from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.tiempo import ZONA_NEGOCIO
from app.modulos.auditoria import repositorio
from app.modulos.auditoria.modelos import RegistroAuditoria

# Campos que nunca se copian al registro de auditoría.
CAMPOS_SENSIBLES = {"hash_contrasena", "contrasena", "contrasena_temporal", "hash_csrf"}


def _limpiar(valores: dict[str, Any] | None) -> dict[str, Any] | None:
    if valores is None:
        return None
    return {
        clave: (valor.isoformat() if isinstance(valor, datetime | date) else valor)
        for clave, valor in valores.items()
        if clave not in CAMPOS_SENSIBLES
    }


def registrar(
    sesion: Session,
    *,
    accion: str,
    entidad: str,
    entidad_id: Any = None,
    usuario_id: int | None = None,
    antes: dict[str, Any] | None = None,
    despues: dict[str, Any] | None = None,
    ip: str | None = None,
    momento: datetime | None = None,
) -> RegistroAuditoria:
    registro = RegistroAuditoria(
        accion=accion,
        entidad=entidad,
        entidad_id=None if entidad_id is None else str(entidad_id),
        usuario_id=usuario_id,
        valor_anterior=_limpiar(antes),
        valor_nuevo=_limpiar(despues),
        ip=ip,
    )
    if momento is not None:
        registro.momento = momento
    sesion.add(registro)
    return registro


def consultar(
    sesion: Session,
    *,
    usuario_id: int | None,
    accion: str | None,
    entidad: str | None,
    entidad_id: str | None,
    desde: date | None,
    hasta: date | None,
    limite: int,
    desplazamiento: int,
) -> tuple[list[RegistroAuditoria], int]:
    # Las fechas del filtro son días de Bogotá; se convierten a un rango de momentos.
    inicio = datetime.combine(desde, time.min, ZONA_NEGOCIO) if desde else None
    fin = datetime.combine(hasta + timedelta(days=1), time.min, ZONA_NEGOCIO) if hasta else None
    return repositorio.buscar(
        sesion,
        usuario_id=usuario_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        inicio=inicio,
        fin=fin,
        limite=limite,
        desplazamiento=desplazamiento,
    )
