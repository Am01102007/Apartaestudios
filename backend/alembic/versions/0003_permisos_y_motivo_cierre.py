"""Permisos del rol de la aplicación y valores válidos de motivo_cierre.

- Otorga al rol de la API (APP_ROL_APLICACION) solo lo que necesita: leer, insertar y
  actualizar; borrar únicamente sesiones; y en la auditoría solo leer e insertar. Si el rol
  no existe todavía, no hace nada (se crea con scripts/roles.sql).
- Restringe sesiones.motivo_cierre a los motivos conocidos.

Revisión: 0003
Anterior: 0002
Creada: 2026-10-17
"""

from collections.abc import Sequence

from alembic import op

from app.core.config import obtener_configuracion
from app.db.permisos import sql_permisos

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "motivo_cierre_valido",
        "sesiones",
        "motivo_cierre IN ('logout', 'inactividad', 'desactivado', 'cambio_contrasena', "
        "'cambio_rol', 'restablecimiento')",
    )
    op.execute(sql_permisos(obtener_configuracion().rol_aplicacion))


def downgrade() -> None:
    op.drop_constraint(op.f("ck_sesiones_motivo_cierre_valido"), "sesiones", type_="check")
