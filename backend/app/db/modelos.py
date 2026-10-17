"""Importa los modelos de todos los dominios para que Alembic los detecte.

Cada módulo de la fase 8 añade aquí su línea, por ejemplo:
    from app.modulos.usuarios import modelos as _usuarios  # noqa: F401
"""

from app.db.base import Base

__all__ = ["Base"]
