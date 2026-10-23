from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modulos.auditoria.modelos import RegistroAuditoria


def buscar(
    sesion: Session,
    *,
    usuario_id: int | None,
    accion: str | None,
    entidad: str | None,
    entidad_id: str | None,
    inicio: datetime | None,
    fin: datetime | None,
    limite: int,
    desplazamiento: int,
) -> tuple[list[RegistroAuditoria], int]:
    filtros = []
    if usuario_id is not None:
        filtros.append(RegistroAuditoria.usuario_id == usuario_id)
    if accion:
        filtros.append(RegistroAuditoria.accion == accion)
    if entidad:
        filtros.append(RegistroAuditoria.entidad == entidad)
    if entidad_id:
        filtros.append(RegistroAuditoria.entidad_id == entidad_id)
    if inicio:
        filtros.append(RegistroAuditoria.momento >= inicio)
    if fin:
        filtros.append(RegistroAuditoria.momento < fin)

    total = sesion.scalar(select(func.count()).select_from(RegistroAuditoria).where(*filtros))
    registros = sesion.scalars(
        select(RegistroAuditoria)
        .where(*filtros)
        .order_by(RegistroAuditoria.momento.desc(), RegistroAuditoria.id.desc())
        .limit(limite)
        .offset(desplazamiento)
    ).all()
    return list(registros), total or 0


def de_entidad(sesion: Session, entidad: str, entidad_id: str) -> list[RegistroAuditoria]:
    """Todos los registros de una entidad, del más antiguo al más reciente."""
    return list(
        sesion.scalars(
            select(RegistroAuditoria)
            .where(RegistroAuditoria.entidad == entidad, RegistroAuditoria.entidad_id == entidad_id)
            .order_by(RegistroAuditoria.momento, RegistroAuditoria.id)
        )
    )
