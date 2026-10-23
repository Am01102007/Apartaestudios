from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, ConId, ConMarcasDeTiempo, Dinero
from app.modulos.inmuebles.modelos import Apartaestudio
from app.modulos.residentes.modelos import Residente
from app.modulos.usuarios.modelos import Usuario

# RC-04: el periodo que un contrato reserva su apartaestudio. Sin fin, el rango es abierto.
SQL_RESERVA = "daterange(fecha_inicio, fin_reserva, '[]')"


class Contrato(ConId, ConMarcasDeTiempo, Base):
    """El estado no se guarda: se calcula con la fecha de hoy (RC-01, `estados.py`).

    Nunca se borra. `fin_reserva` es la entrega, o el día anterior al contrato que lo renueva;
    nulo mientras no tenga ninguna de las dos.
    """

    __tablename__ = "contratos"
    __table_args__ = (
        CheckConstraint("fecha_terminacion > fecha_inicio", name="terminacion_posterior"),
        CheckConstraint("canon_inicial > 0", name="canon_positivo"),
        CheckConstraint(
            "porcentaje_incremento >= 0 AND porcentaje_incremento <= 100",
            name="porcentaje_valido",
        ),
        CheckConstraint(
            "(fecha_aviso IS NULL AND fecha_entrega IS NULL AND motivo_terminacion IS NULL"
            " AND terminacion_registrada_por_id IS NULL)"
            " OR (fecha_aviso IS NOT NULL AND fecha_entrega IS NOT NULL"
            " AND motivo_terminacion IS NOT NULL AND terminacion_registrada_por_id IS NOT NULL)",
            name="terminacion_completa",
        ),
        CheckConstraint(
            "(anulado_en IS NULL AND anulado_por_id IS NULL AND motivo_anulacion IS NULL)"
            " OR (anulado_en IS NOT NULL AND anulado_por_id IS NOT NULL"
            " AND motivo_anulacion IS NOT NULL)",
            name="anulacion_completa",
        ),
        CheckConstraint("fecha_entrega >= fecha_inicio", name="entrega_desde_inicio"),
        CheckConstraint(
            "fin_reserva IS NULL OR fin_reserva >= fecha_inicio", name="reserva_desde_inicio"
        ),
        # RN-04 y RN-05: dos contratos no anulados del mismo apartaestudio no se cruzan.
        ExcludeConstraint(
            ("apartaestudio_id", "="),
            (text(SQL_RESERVA), "&&"),
            name="ex_contratos_reserva",
            using="gist",
            where=text("anulado_en IS NULL"),
        ),
        # Un contrato tiene a lo sumo una renovación que no esté anulada.
        Index(
            "uq_contratos_renovacion",
            "contrato_anterior_id",
            unique=True,
            postgresql_where=text("anulado_en IS NULL"),
        ),
    )

    apartaestudio_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("apartaestudios.id", ondelete="RESTRICT"), index=True
    )
    residente_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("residentes.id", ondelete="RESTRICT"), index=True
    )
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_terminacion: Mapped[date] = mapped_column(Date)
    canon_inicial: Mapped[Decimal] = mapped_column(Dinero)
    porcentaje_incremento: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    notas: Mapped[str | None] = mapped_column(Text)
    contrato_anterior_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("contratos.id", ondelete="RESTRICT")
    )
    fecha_aviso: Mapped[date | None] = mapped_column(Date)
    fecha_entrega: Mapped[date | None] = mapped_column(Date)
    motivo_terminacion: Mapped[str | None] = mapped_column(String(500))
    terminacion_registrada_por_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("usuarios.id")
    )
    anulado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    anulado_por_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("usuarios.id"))
    motivo_anulacion: Mapped[str | None] = mapped_column(String(500))
    fin_reserva: Mapped[date | None] = mapped_column(Date)
    creado_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuarios.id"))

    creado_por: Mapped[Usuario] = relationship(foreign_keys=[creado_por_id], lazy="joined")
    apartaestudio: Mapped[Apartaestudio] = relationship(lazy="joined", innerjoin=True)
    residente: Mapped[Residente] = relationship(lazy="joined", innerjoin=True)


class Prorroga(ConId, Base):
    """Cada prórroga queda como fila propia (RC-12); nunca se borra ni se edita."""

    __tablename__ = "prorrogas"
    __table_args__ = (
        CheckConstraint("terminacion_nueva > terminacion_anterior", name="extiende_terminacion"),
    )

    contrato_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("contratos.id", ondelete="RESTRICT"), index=True
    )
    terminacion_anterior: Mapped[date] = mapped_column(Date)
    terminacion_nueva: Mapped[date] = mapped_column(Date)
    registrada_por_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuarios.id"))
    registrada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    registrada_por: Mapped[Usuario] = relationship(lazy="joined")
