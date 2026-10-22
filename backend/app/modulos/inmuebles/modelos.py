from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.documentos import (
    SQL_NUMERO_NORMALIZADO,
    SQL_TIPO_VALIDO,
    TipoDocumento,
    columna_tipo,
)
from app.db.base import Base, ConId, ConMarcasDeTiempo


class Ocupacion(StrEnum):
    LIBRE = "libre"
    OCUPADO = "ocupado"


class Propietario(ConId, ConMarcasDeTiempo, Base):
    __tablename__ = "propietarios"
    __table_args__ = (
        UniqueConstraint("tipo_documento", "numero_documento"),
        CheckConstraint(SQL_TIPO_VALIDO, name="tipo_documento_valido"),
        CheckConstraint(SQL_NUMERO_NORMALIZADO, name="numero_documento_normalizado"),
    )

    nombre: Mapped[str] = mapped_column(String(150))
    tipo_documento: Mapped[TipoDocumento] = mapped_column(columna_tipo())
    numero_documento: Mapped[str] = mapped_column(String(20))
    telefono: Mapped[str | None] = mapped_column(String(20))
    correo: Mapped[str | None] = mapped_column(String(254))
    direccion: Mapped[str | None] = mapped_column(String(200))
    notas: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), default=True)


class Apartaestudio(ConId, ConMarcasDeTiempo, Base):
    __tablename__ = "apartaestudios"
    __table_args__ = (
        CheckConstraint("codigo = upper(codigo)", name="codigo_mayusculas"),
        CheckConstraint("area_m2 > 0", name="area_positiva"),
        # Una marca de mantenimiento nunca queda a medias (RP-05).
        CheckConstraint(
            "(en_mantenimiento AND mantenimiento_desde IS NOT NULL "
            "AND mantenimiento_motivo IS NOT NULL AND mantenimiento_por_id IS NOT NULL) "
            "OR (NOT en_mantenimiento AND mantenimiento_desde IS NULL "
            "AND mantenimiento_motivo IS NULL AND mantenimiento_por_id IS NULL)",
            name="mantenimiento_completo",
        ),
    )

    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    propietario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("propietarios.id", ondelete="RESTRICT"), index=True
    )
    direccion: Mapped[str] = mapped_column(String(200))
    area_m2: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    descripcion: Mapped[str | None] = mapped_column(Text)
    en_mantenimiento: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), default=False
    )
    mantenimiento_desde: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mantenimiento_motivo: Mapped[str | None] = mapped_column(String(300))
    mantenimiento_por_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("usuarios.id"))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), default=True)

    propietario: Mapped[Propietario] = relationship(lazy="joined", innerjoin=True)
