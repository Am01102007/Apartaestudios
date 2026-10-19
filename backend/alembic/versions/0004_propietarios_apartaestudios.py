"""Propietarios y apartaestudios (módulo 2).

No hay columna de ocupación: se calcula a partir de los contratos (RN-02). La marca de
mantenimiento tiene una restricción que impide dejarla a medias (RP-05).

Revisión: 0004
Anterior: 0003
Creada: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.config import obtener_configuracion
from app.db.permisos import sql_permisos

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _marcas_de_tiempo() -> list[sa.Column]:
    return [
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "propietarios",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("tipo_documento", sa.String(length=5), nullable=False),
        sa.Column("numero_documento", sa.String(length=20), nullable=False),
        sa.Column("telefono", sa.String(length=20), nullable=True),
        sa.Column("correo", sa.String(length=254), nullable=True),
        sa.Column("direccion", sa.String(length=200), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_marcas_de_tiempo(),
        sa.CheckConstraint(
            "tipo_documento IN ('CC', 'CE', 'NIT', 'PA', 'PPT')",
            name=op.f("ck_propietarios_tipo_documento_valido"),
        ),
        sa.CheckConstraint(
            "numero_documento ~ '^[A-Z0-9]{3,20}$'",
            name=op.f("ck_propietarios_numero_documento_normalizado"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_propietarios")),
        sa.UniqueConstraint(
            "tipo_documento",
            "numero_documento",
            name=op.f("uq_propietarios_tipo_documento_numero_documento"),
        ),
    )
    op.create_table(
        "apartaestudios",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("codigo", sa.String(length=20), nullable=False),
        sa.Column("propietario_id", sa.BigInteger(), nullable=False),
        sa.Column("direccion", sa.String(length=200), nullable=False),
        sa.Column("area_m2", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column(
            "en_mantenimiento", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("mantenimiento_desde", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mantenimiento_motivo", sa.String(length=300), nullable=True),
        sa.Column("mantenimiento_por_id", sa.BigInteger(), nullable=True),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_marcas_de_tiempo(),
        sa.CheckConstraint(
            "codigo = upper(codigo)", name=op.f("ck_apartaestudios_codigo_mayusculas")
        ),
        sa.CheckConstraint("area_m2 > 0", name=op.f("ck_apartaestudios_area_positiva")),
        sa.CheckConstraint(
            "(en_mantenimiento AND mantenimiento_desde IS NOT NULL "
            "AND mantenimiento_motivo IS NOT NULL AND mantenimiento_por_id IS NOT NULL) "
            "OR (NOT en_mantenimiento AND mantenimiento_desde IS NULL "
            "AND mantenimiento_motivo IS NULL AND mantenimiento_por_id IS NULL)",
            name=op.f("ck_apartaestudios_mantenimiento_completo"),
        ),
        sa.ForeignKeyConstraint(
            ["propietario_id"],
            ["propietarios.id"],
            name=op.f("fk_apartaestudios_propietario_id_propietarios"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["mantenimiento_por_id"],
            ["usuarios.id"],
            name=op.f("fk_apartaestudios_mantenimiento_por_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_apartaestudios")),
        sa.UniqueConstraint("codigo", name=op.f("uq_apartaestudios_codigo")),
    )
    op.create_index(op.f("ix_apartaestudios_propietario_id"), "apartaestudios", ["propietario_id"])
    op.execute(sql_permisos(obtener_configuracion().rol_aplicacion))


def downgrade() -> None:
    op.drop_index(op.f("ix_apartaestudios_propietario_id"), table_name="apartaestudios")
    op.drop_table("apartaestudios")
    op.drop_table("propietarios")
