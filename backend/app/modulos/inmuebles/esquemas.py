from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.core.documentos import TipoDocumento, error_documento
from app.core.entradas import Correo, Entrada, NumeroDocumento, Telefono, si_es_texto, texto
from app.modulos.inmuebles.modelos import Ocupacion
from app.modulos.inmuebles.reglas import normalizar_codigo

# RP-03.
Codigo = Annotated[
    str,
    si_es_texto(normalizar_codigo),
    StringConstraints(pattern=r"^[A-Z0-9][A-Z0-9 -]{0,19}$"),
]
Area = Annotated[Decimal, Field(gt=0, max_digits=6, decimal_places=2)]


# --- Propietarios ---------------------------------------------------------------------------


class PropietarioCrear(Entrada):
    nombre: texto(1, 150)
    tipo_documento: TipoDocumento
    numero_documento: NumeroDocumento
    telefono: Telefono | None = None
    correo: Correo | None = None
    direccion: texto(1, 200) | None = None
    notas: texto(1, 1000) | None = None

    @model_validator(mode="after")
    def _documento(self) -> "PropietarioCrear":
        if mensaje := error_documento(self.tipo_documento, self.numero_documento):
            raise ValueError(mensaje)
        return self


class PropietarioEditar(Entrada):
    obligatorios = ("nombre", "tipo_documento", "numero_documento")

    nombre: texto(1, 150) | None = None
    tipo_documento: TipoDocumento | None = None
    numero_documento: NumeroDocumento | None = None
    telefono: Telefono | None = None
    correo: Correo | None = None
    direccion: texto(1, 200) | None = None
    notas: texto(1, 1000) | None = None


class PropietarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    tipo_documento: TipoDocumento
    numero_documento: str
    telefono: str | None
    correo: str | None
    direccion: str | None
    notas: str | None
    activo: bool
    creado_en: datetime


class ApartaestudioResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    direccion: str
    activo: bool
    en_mantenimiento: bool
    ocupacion: Ocupacion


class PropietarioDetalle(PropietarioSalida):
    apartaestudios: list[ApartaestudioResumen]


# --- Apartaestudios -------------------------------------------------------------------------


class ApartaestudioCrear(Entrada):
    codigo: Codigo
    propietario_id: int
    direccion: texto(1, 200)
    area_m2: Area | None = None
    descripcion: texto(1, 1000) | None = None


class ApartaestudioEditar(Entrada):
    obligatorios = ("codigo", "propietario_id", "direccion")

    codigo: Codigo | None = None
    propietario_id: int | None = None
    direccion: texto(1, 200) | None = None
    area_m2: Area | None = None
    descripcion: texto(1, 1000) | None = None


class CambioMantenimiento(Entrada):
    activo: bool
    motivo: texto(3, 300)


class PropietarioReferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    activo: bool


class ApartaestudioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    propietario: PropietarioReferencia
    direccion: str
    area_m2: Decimal | None
    descripcion: str | None
    activo: bool
    # RP-04: calculada en cada consulta; no existe como dato editable.
    ocupacion: Ocupacion
    en_mantenimiento: bool
    mantenimiento_desde: datetime | None
    mantenimiento_motivo: str | None
    mantenimiento_por_id: int | None
    creado_en: datetime
