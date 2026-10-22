from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.core.documentos import TipoDocumento, error_documento
from app.core.entradas import Entrada, NumeroDocumento, texto


class BloqueoCrear(Entrada):
    tipo_documento: TipoDocumento
    numero_documento: NumeroDocumento
    nombre: texto(1, 150)
    motivo: texto(3, 500)

    @model_validator(mode="after")
    def _documento(self) -> "BloqueoCrear":
        if mensaje := error_documento(self.tipo_documento, self.numero_documento):
            raise ValueError(mensaje)
        return self


class Levantamiento(Entrada):
    motivo: texto(3, 500)


class UsuarioReferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class BloqueoSalida(BaseModel):
    """`motivo` y `motivo_levantamiento` solo los ve el administrador (D-3); al empleado le
    llegan nulos."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_documento: TipoDocumento
    numero_documento: str
    nombre: str
    activo: bool
    motivo: str | None
    bloqueado_en: datetime
    bloqueado_por: UsuarioReferencia
    levantado_en: datetime | None
    levantado_por: UsuarioReferencia | None
    motivo_levantamiento: str | None


class Verificacion(BaseModel):
    bloqueado: bool
    bloqueo_id: int | None = None
    desde: datetime | None = None
