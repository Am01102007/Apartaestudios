from datetime import datetime
from enum import StrEnum

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.documentos import (
    SQL_NUMERO_NORMALIZADO,
    SQL_TIPO_VALIDO,
    TipoDocumento,
    columna_tipo,
)
from app.db.base import Base, ConId
from app.modulos.usuarios.modelos import Usuario


class EstadoBloqueo(StrEnum):
    ACTIVOS = "activos"
    LEVANTADOS = "levantados"
    TODOS = "todos"


class Bloqueo(ConId, Base):
    """Nunca se borra ni se edita: levantarlo completa sus columnas de levantamiento (RR-05)."""

    __tablename__ = "bloqueos"
    __table_args__ = (
        CheckConstraint(SQL_TIPO_VALIDO, name="tipo_documento_valido"),
        CheckConstraint(SQL_NUMERO_NORMALIZADO, name="numero_documento_normalizado"),
        CheckConstraint(
            "(levantado_en IS NULL AND levantado_por_id IS NULL AND motivo_levantamiento IS NULL)"
            " OR (levantado_en IS NOT NULL AND levantado_por_id IS NOT NULL"
            " AND motivo_levantamiento IS NOT NULL)",
            name="levantamiento_completo",
        ),
        # RR-04: como máximo un bloqueo activo por documento.
        Index(
            "uq_bloqueos_documento_activo",
            "tipo_documento",
            "numero_documento",
            unique=True,
            postgresql_where=text("levantado_en IS NULL"),
        ),
        Index("ix_bloqueos_documento", "tipo_documento", "numero_documento"),
    )

    tipo_documento: Mapped[TipoDocumento] = mapped_column(columna_tipo())
    numero_documento: Mapped[str] = mapped_column(String(20))
    nombre: Mapped[str] = mapped_column(String(150))
    motivo: Mapped[str] = mapped_column(String(500))
    bloqueado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    bloqueado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuarios.id"))
    levantado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    levantado_por_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("usuarios.id"))
    motivo_levantamiento: Mapped[str | None] = mapped_column(String(500))

    bloqueado_por: Mapped[Usuario] = relationship(foreign_keys=[bloqueado_por_id], lazy="joined")
    levantado_por: Mapped[Usuario | None] = relationship(
        foreign_keys=[levantado_por_id], lazy="joined"
    )

    @property
    def activo(self) -> bool:
        return self.levantado_en is None
