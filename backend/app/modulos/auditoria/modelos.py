from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, ConId
from app.modulos.usuarios.modelos import Usuario


class RegistroAuditoria(ConId, Base):
    """Registro inmodificable: un disparador de PostgreSQL rechaza UPDATE y DELETE (RF-23)."""

    __tablename__ = "auditoria"
    __table_args__ = (
        Index("ix_auditoria_momento", "momento"),
        Index("ix_auditoria_entidad", "entidad", "entidad_id"),
        Index("ix_auditoria_usuario_id", "usuario_id"),
    )

    momento: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    usuario_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("usuarios.id"))
    accion: Mapped[str] = mapped_column(String(60))
    entidad: Mapped[str] = mapped_column(String(60))
    entidad_id: Mapped[str | None] = mapped_column(String(60))
    valor_anterior: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    valor_nuevo: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ip: Mapped[str | None] = mapped_column(String(45))

    usuario: Mapped[Usuario | None] = relationship(lazy="joined")
