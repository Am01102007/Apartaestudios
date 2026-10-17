"""Base: extensiones de PostgreSQL que necesita el modelo.

btree_gist permite la restricción de exclusión que impide contratos superpuestos sobre el
mismo apartaestudio (RN-04, RN-05). Las tablas de cada dominio llegan en las migraciones
de la fase 8.

Revisión: 0001
Anterior: ninguna
Creada: 2026-10-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
