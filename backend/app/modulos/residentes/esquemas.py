from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.core.documentos import TipoDocumento, error_documento
from app.core.entradas import Correo, Entrada, NumeroDocumento, Telefono, texto
from app.modulos.bloqueos.esquemas import BloqueoSalida
from app.modulos.contratos.esquemas import ContratoSalida


class ResidenteCrear(Entrada):
    nombre: texto(1, 150)
    tipo_documento: TipoDocumento
    numero_documento: NumeroDocumento
    telefono: Telefono
    correo: Correo | None = None
    contacto_emergencia_nombre: texto(1, 150) | None = None
    contacto_emergencia_telefono: Telefono | None = None
    notas: texto(1, 1000) | None = None

    @model_validator(mode="after")
    def _coherencia(self) -> "ResidenteCrear":
        if mensaje := error_documento(self.tipo_documento, self.numero_documento):
            raise ValueError(mensaje)
        if (self.contacto_emergencia_nombre is None) != (self.contacto_emergencia_telefono is None):
            raise ValueError("El contacto de emergencia necesita nombre y teléfono")
        return self


class ResidenteEditar(Entrada):
    obligatorios = ("nombre", "tipo_documento", "numero_documento", "telefono")

    nombre: texto(1, 150) | None = None
    tipo_documento: TipoDocumento | None = None
    numero_documento: NumeroDocumento | None = None
    telefono: Telefono | None = None
    correo: Correo | None = None
    contacto_emergencia_nombre: texto(1, 150) | None = None
    contacto_emergencia_telefono: Telefono | None = None
    notas: texto(1, 1000) | None = None


class ResidenteSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    tipo_documento: TipoDocumento
    numero_documento: str
    telefono: str
    correo: str | None
    contacto_emergencia_nombre: str | None
    contacto_emergencia_telefono: str | None
    notas: str | None
    creado_en: datetime


class ResidenteDetalle(ResidenteSalida):
    bloqueo_activo: BloqueoSalida | None  # R-04
    # Por iniciar, vigentes, vencidos o en terminación (módulo 4).
    contratos_actuales: list[ContratoSalida]

    @classmethod
    def construir(
        cls, residente: Any, bloqueo: BloqueoSalida | None, contratos: list[Any]
    ) -> "ResidenteDetalle":
        return cls.model_validate(
            {
                **ResidenteSalida.model_validate(residente).model_dump(),
                "bloqueo_activo": bloqueo,
                "contratos_actuales": [ContratoSalida.model_validate(c) for c in contratos],
            }
        )
