"""Importa los modelos de todos los dominios para que Alembic los detecte.

Cada módulo nuevo añade aquí su línea.
"""

from app.db.base import Base
from app.modulos.auditoria import modelos as _auditoria  # noqa: F401
from app.modulos.usuarios import modelos as _usuarios  # noqa: F401

__all__ = ["Base"]
