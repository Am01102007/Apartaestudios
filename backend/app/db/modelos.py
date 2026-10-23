"""Importa los modelos de todos los dominios para que Alembic los detecte.

Cada módulo nuevo añade aquí su línea.
"""

from app.db.base import Base
from app.modulos.auditoria import modelos as _auditoria  # noqa: F401
from app.modulos.bloqueos import modelos as _bloqueos  # noqa: F401
from app.modulos.contratos import modelos as _contratos  # noqa: F401
from app.modulos.inmuebles import modelos as _inmuebles  # noqa: F401
from app.modulos.residentes import modelos as _residentes  # noqa: F401
from app.modulos.usuarios import modelos as _usuarios  # noqa: F401

__all__ = ["Base"]
