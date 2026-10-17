from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class RegistroAuditoriaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    momento: datetime
    usuario_id: int | None
    accion: str
    entidad: str
    entidad_id: str | None
    valor_anterior: dict[str, Any] | None
    valor_nuevo: dict[str, Any] | None
    ip: str | None


class PaginaAuditoria(BaseModel):
    total: int
    registros: list[RegistroAuditoriaSalida]
