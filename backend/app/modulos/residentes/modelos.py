from sqlalchemy import CheckConstraint, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.documentos import (
    SQL_NUMERO_NORMALIZADO,
    SQL_TIPO_VALIDO,
    TipoDocumento,
    columna_tipo,
)
from app.db.base import Base, ConId, ConMarcasDeTiempo


class Residente(ConId, ConMarcasDeTiempo, Base):
    """No tiene estado activo: "residente actual" se calculará a partir de sus contratos (RR-02)."""

    __tablename__ = "residentes"
    __table_args__ = (
        UniqueConstraint("tipo_documento", "numero_documento"),
        CheckConstraint(SQL_TIPO_VALIDO, name="tipo_documento_valido"),
        CheckConstraint(SQL_NUMERO_NORMALIZADO, name="numero_documento_normalizado"),
        CheckConstraint(
            "(contacto_emergencia_nombre IS NULL) = (contacto_emergencia_telefono IS NULL)",
            name="contacto_emergencia_completo",
        ),
    )

    nombre: Mapped[str] = mapped_column(String(150))
    tipo_documento: Mapped[TipoDocumento] = mapped_column(columna_tipo())
    numero_documento: Mapped[str] = mapped_column(String(20))
    telefono: Mapped[str] = mapped_column(String(20))
    correo: Mapped[str | None] = mapped_column(String(254))
    contacto_emergencia_nombre: Mapped[str | None] = mapped_column(String(150))
    contacto_emergencia_telefono: Mapped[str | None] = mapped_column(String(20))
    notas: Mapped[str | None] = mapped_column(Text)
