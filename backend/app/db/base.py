"""Base declarativa de SQLAlchemy y convenciones comunes del modelo (fase 5)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, MetaData, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nombres de índices y restricciones predecibles, para que las migraciones sean estables.
CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Dinero en pesos colombianos sin decimales, con tipo decimal exacto (RNF-08).
Dinero = Numeric(14, 0)
# Porcentajes como 4.5000 (%).
Porcentaje = Numeric(7, 4)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)
    type_annotation_map = {Decimal: Dinero}


class ConId:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class ConMarcasDeTiempo:
    """Momentos de creación y actualización, en UTC (TIMESTAMPTZ)."""

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
