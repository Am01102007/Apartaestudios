"""Contratos y prórrogas (módulo 4).

La restricción de exclusión `ex_contratos_reserva` (con `btree_gist`, instalada en 0001)
impide que dos contratos no anulados del mismo apartaestudio crucen sus reservas (RN-04,
RN-05). El rol de la aplicación no puede borrar contratos ni prórrogas.

Revisión: 0006
Anterior: 0005
Creada: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.config import obtener_configuracion
from app.db.permisos import sql_permisos

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contratos",
        sa.Column("apartaestudio_id", sa.BigInteger(), nullable=False),
        sa.Column("residente_id", sa.BigInteger(), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_terminacion", sa.Date(), nullable=False),
        sa.Column("canon_inicial", sa.Numeric(precision=14, scale=0), nullable=False),
        sa.Column("porcentaje_incremento", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("contrato_anterior_id", sa.BigInteger(), nullable=True),
        sa.Column("fecha_aviso", sa.Date(), nullable=True),
        sa.Column("fecha_entrega", sa.Date(), nullable=True),
        sa.Column("motivo_terminacion", sa.String(length=500), nullable=True),
        sa.Column("terminacion_registrada_por_id", sa.BigInteger(), nullable=True),
        sa.Column("anulado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anulado_por_id", sa.BigInteger(), nullable=True),
        sa.Column("motivo_anulacion", sa.String(length=500), nullable=True),
        sa.Column("fin_reserva", sa.Date(), nullable=True),
        sa.Column("creado_por_id", sa.BigInteger(), nullable=False),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        postgresql.ExcludeConstraint(
            (sa.column("apartaestudio_id"), "="),
            (sa.text("daterange(fecha_inicio, fin_reserva, '[]')"), "&&"),
            where=sa.text("anulado_en IS NULL"),
            using="gist",
            name="ex_contratos_reserva",
        ),
        sa.CheckConstraint(
            "(anulado_en IS NULL AND anulado_por_id IS NULL AND motivo_anulacion IS NULL)"
            " OR (anulado_en IS NOT NULL AND anulado_por_id IS NOT NULL"
            " AND motivo_anulacion IS NOT NULL)",
            name=op.f("ck_contratos_anulacion_completa"),
        ),
        sa.CheckConstraint(
            "(fecha_aviso IS NULL AND fecha_entrega IS NULL AND motivo_terminacion IS NULL"
            " AND terminacion_registrada_por_id IS NULL)"
            " OR (fecha_aviso IS NOT NULL AND fecha_entrega IS NOT NULL"
            " AND motivo_terminacion IS NOT NULL AND terminacion_registrada_por_id IS NOT NULL)",
            name=op.f("ck_contratos_terminacion_completa"),
        ),
        sa.CheckConstraint("canon_inicial > 0", name=op.f("ck_contratos_canon_positivo")),
        sa.CheckConstraint(
            "fecha_entrega >= fecha_inicio", name=op.f("ck_contratos_entrega_desde_inicio")
        ),
        sa.CheckConstraint(
            "fecha_terminacion > fecha_inicio", name=op.f("ck_contratos_terminacion_posterior")
        ),
        sa.CheckConstraint(
            "fin_reserva IS NULL OR fin_reserva >= fecha_inicio",
            name=op.f("ck_contratos_reserva_desde_inicio"),
        ),
        sa.CheckConstraint(
            "porcentaje_incremento >= 0 AND porcentaje_incremento <= 100",
            name=op.f("ck_contratos_porcentaje_valido"),
        ),
        sa.ForeignKeyConstraint(
            ["anulado_por_id"], ["usuarios.id"], name=op.f("fk_contratos_anulado_por_id_usuarios")
        ),
        sa.ForeignKeyConstraint(
            ["apartaestudio_id"],
            ["apartaestudios.id"],
            name=op.f("fk_contratos_apartaestudio_id_apartaestudios"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["contrato_anterior_id"],
            ["contratos.id"],
            name=op.f("fk_contratos_contrato_anterior_id_contratos"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["creado_por_id"], ["usuarios.id"], name=op.f("fk_contratos_creado_por_id_usuarios")
        ),
        sa.ForeignKeyConstraint(
            ["residente_id"],
            ["residentes.id"],
            name=op.f("fk_contratos_residente_id_residentes"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["terminacion_registrada_por_id"],
            ["usuarios.id"],
            name=op.f("fk_contratos_terminacion_registrada_por_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contratos")),
    )
    op.create_index(
        op.f("ix_contratos_apartaestudio_id"), "contratos", ["apartaestudio_id"], unique=False
    )
    op.create_index(op.f("ix_contratos_residente_id"), "contratos", ["residente_id"], unique=False)
    op.create_index(
        "uq_contratos_renovacion",
        "contratos",
        ["contrato_anterior_id"],
        unique=True,
        postgresql_where=sa.text("anulado_en IS NULL"),
    )
    op.create_table(
        "prorrogas",
        sa.Column("contrato_id", sa.BigInteger(), nullable=False),
        sa.Column("terminacion_anterior", sa.Date(), nullable=False),
        sa.Column("terminacion_nueva", sa.Date(), nullable=False),
        sa.Column("registrada_por_id", sa.BigInteger(), nullable=False),
        sa.Column("registrada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.CheckConstraint(
            "terminacion_nueva > terminacion_anterior",
            name=op.f("ck_prorrogas_extiende_terminacion"),
        ),
        sa.ForeignKeyConstraint(
            ["contrato_id"],
            ["contratos.id"],
            name=op.f("fk_prorrogas_contrato_id_contratos"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["registrada_por_id"],
            ["usuarios.id"],
            name=op.f("fk_prorrogas_registrada_por_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prorrogas")),
    )
    op.create_index(op.f("ix_prorrogas_contrato_id"), "prorrogas", ["contrato_id"], unique=False)
    op.execute(sql_permisos(obtener_configuracion().rol_aplicacion))


def downgrade() -> None:
    op.drop_index(op.f("ix_prorrogas_contrato_id"), table_name="prorrogas")
    op.drop_table("prorrogas")
    op.drop_index(
        "uq_contratos_renovacion",
        table_name="contratos",
        postgresql_where=sa.text("anulado_en IS NULL"),
    )
    op.drop_index(op.f("ix_contratos_residente_id"), table_name="contratos")
    op.drop_index(op.f("ix_contratos_apartaestudio_id"), table_name="contratos")
    op.drop_table("contratos")
