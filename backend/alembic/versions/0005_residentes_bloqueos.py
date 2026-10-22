"""Residentes y bloqueos (módulo 3).

Los bloqueos se aplican a un documento y nunca se borran: el índice único parcial deja como
máximo uno activo por documento (RR-04), y el rol de la aplicación no tiene permiso de borrado.

Revisión: 0005
Anterior: 0004
Creada: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.config import obtener_configuracion
from app.core.documentos import SQL_NUMERO_NORMALIZADO, SQL_TIPO_VALIDO
from app.db.permisos import sql_permisos

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _documento(tabla: str) -> list:
    return [
        sa.Column("tipo_documento", sa.String(length=5), nullable=False),
        sa.Column("numero_documento", sa.String(length=20), nullable=False),
        sa.CheckConstraint(SQL_TIPO_VALIDO, name=op.f(f"ck_{tabla}_tipo_documento_valido")),
        sa.CheckConstraint(
            SQL_NUMERO_NORMALIZADO, name=op.f(f"ck_{tabla}_numero_documento_normalizado")
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "residentes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        *_documento("residentes"),
        sa.Column("telefono", sa.String(length=20), nullable=False),
        sa.Column("correo", sa.String(length=254), nullable=True),
        sa.Column("contacto_emergencia_nombre", sa.String(length=150), nullable=True),
        sa.Column("contacto_emergencia_telefono", sa.String(length=20), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column(
            "creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(contacto_emergencia_nombre IS NULL) = (contacto_emergencia_telefono IS NULL)",
            name=op.f("ck_residentes_contacto_emergencia_completo"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_residentes")),
        sa.UniqueConstraint(
            "tipo_documento",
            "numero_documento",
            name=op.f("uq_residentes_tipo_documento_numero_documento"),
        ),
    )
    op.create_table(
        "bloqueos",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        *_documento("bloqueos"),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("motivo", sa.String(length=500), nullable=False),
        sa.Column("bloqueado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bloqueado_por_id", sa.BigInteger(), nullable=False),
        sa.Column("levantado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("levantado_por_id", sa.BigInteger(), nullable=True),
        sa.Column("motivo_levantamiento", sa.String(length=500), nullable=True),
        sa.CheckConstraint(
            "(levantado_en IS NULL AND levantado_por_id IS NULL AND motivo_levantamiento IS NULL)"
            " OR (levantado_en IS NOT NULL AND levantado_por_id IS NOT NULL"
            " AND motivo_levantamiento IS NOT NULL)",
            name=op.f("ck_bloqueos_levantamiento_completo"),
        ),
        sa.ForeignKeyConstraint(
            ["bloqueado_por_id"],
            ["usuarios.id"],
            name=op.f("fk_bloqueos_bloqueado_por_id_usuarios"),
        ),
        sa.ForeignKeyConstraint(
            ["levantado_por_id"],
            ["usuarios.id"],
            name=op.f("fk_bloqueos_levantado_por_id_usuarios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bloqueos")),
    )
    op.create_index("ix_bloqueos_documento", "bloqueos", ["tipo_documento", "numero_documento"])
    op.create_index(
        "uq_bloqueos_documento_activo",
        "bloqueos",
        ["tipo_documento", "numero_documento"],
        unique=True,
        postgresql_where=sa.text("levantado_en IS NULL"),
    )
    op.execute(sql_permisos(obtener_configuracion().rol_aplicacion))


def downgrade() -> None:
    op.drop_index("uq_bloqueos_documento_activo", table_name="bloqueos")
    op.drop_index("ix_bloqueos_documento", table_name="bloqueos")
    op.drop_table("bloqueos")
    op.drop_table("residentes")
