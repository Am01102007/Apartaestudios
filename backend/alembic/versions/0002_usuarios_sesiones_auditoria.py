"""Usuarios, sesiones y auditoría (módulo 1).

La tabla de auditoría queda protegida por un disparador que rechaza UPDATE y DELETE, de modo
que ni un error del código ni una consulta manual pueden alterar el historial (RF-23).

Revisión: 0002
Anterior: 0001
Creada: 2026-10-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("nombre_usuario", sa.String(length=30), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("correo", sa.String(length=254), nullable=True),
        sa.Column("hash_contrasena", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "debe_cambiar_contrasena", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "intentos_fallidos", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_ingreso", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "rol IN ('administrador', 'empleado')", name=op.f("ck_usuarios_rol_valido")
        ),
        sa.CheckConstraint(
            "intentos_fallidos >= 0", name=op.f("ck_usuarios_intentos_no_negativos")
        ),
        sa.CheckConstraint(
            "nombre_usuario = lower(nombre_usuario)",
            name=op.f("ck_usuarios_nombre_usuario_minusculas"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuarios")),
        sa.UniqueConstraint("nombre_usuario", name=op.f("uq_usuarios_nombre_usuario")),
    )
    op.create_table(
        "auditoria",
        sa.Column(
            "momento", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("usuario_id", sa.BigInteger(), nullable=True),
        sa.Column("accion", sa.String(length=60), nullable=False),
        sa.Column("entidad", sa.String(length=60), nullable=False),
        sa.Column("entidad_id", sa.String(length=60), nullable=True),
        sa.Column("valor_anterior", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("valor_nuevo", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], name=op.f("fk_auditoria_usuario_id_usuarios")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auditoria")),
    )
    op.create_index("ix_auditoria_entidad", "auditoria", ["entidad", "entidad_id"], unique=False)
    op.create_index("ix_auditoria_momento", "auditoria", ["momento"], unique=False)
    op.create_index("ix_auditoria_usuario_id", "auditoria", ["usuario_id"], unique=False)
    op.create_table(
        "sesiones",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("hash_csrf", sa.String(length=64), nullable=False),
        sa.Column(
            "creada_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("ultimo_uso", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cerrada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("motivo_cierre", sa.String(length=30), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("agente_usuario", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"], name=op.f("fk_sesiones_usuario_id_usuarios")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sesiones")),
    )
    op.create_index(
        "ix_sesiones_usuario_abiertas",
        "sesiones",
        ["usuario_id"],
        unique=False,
        postgresql_where=sa.text("cerrada_en IS NULL"),
    )
    op.execute(
        """
        CREATE FUNCTION auditoria_inmodificable() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'El registro de auditoría no se puede modificar ni borrar';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER auditoria_inmodificable
        BEFORE UPDATE OR DELETE OR TRUNCATE ON auditoria
        FOR EACH STATEMENT EXECUTE FUNCTION auditoria_inmodificable()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER auditoria_inmodificable ON auditoria")
    op.execute("DROP FUNCTION auditoria_inmodificable()")
    op.drop_index(
        "ix_sesiones_usuario_abiertas",
        table_name="sesiones",
        postgresql_where=sa.text("cerrada_en IS NULL"),
    )
    op.drop_table("sesiones")
    op.drop_index("ix_auditoria_usuario_id", table_name="auditoria")
    op.drop_index("ix_auditoria_momento", table_name="auditoria")
    op.drop_index("ix_auditoria_entidad", table_name="auditoria")
    op.drop_table("auditoria")
    op.drop_table("usuarios")
