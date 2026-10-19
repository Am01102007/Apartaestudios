from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, ClassVar

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from app.modulos.inmuebles.modelos import Ocupacion, TipoDocumento
from app.modulos.inmuebles.reglas import normalizar_codigo, normalizar_documento


def _si_es_texto(funcion):
    return BeforeValidator(lambda valor: funcion(valor) if isinstance(valor, str) else valor)


def _texto(minimo: int, maximo: int):
    return Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=minimo, max_length=maximo)
    ]


# RP-02: se normaliza antes de validar el formato.
NumeroDocumento = Annotated[
    str,
    _si_es_texto(normalizar_documento),
    StringConstraints(pattern=r"^[A-Z0-9]{3,20}$"),
]
# RP-03.
Codigo = Annotated[
    str,
    _si_es_texto(normalizar_codigo),
    StringConstraints(pattern=r"^[A-Z0-9][A-Z0-9 -]{0,19}$"),
]
Telefono = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9 ()-]{7,20}$")]
Correo = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_lower=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    ),
]
Area = Annotated[Decimal, Field(gt=0, max_digits=6, decimal_places=2)]


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    obligatorios: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def _sin_nulos_obligatorios(self) -> Any:
        # En las ediciones, omitir un campo lo deja igual; enviarlo nulo solo vale si es opcional.
        for campo in self.obligatorios:
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"{campo} no puede ser nulo")
        return self


def _documento_numerico(tipo: TipoDocumento | None, numero: str | None) -> None:
    if tipo in (TipoDocumento.CC, TipoDocumento.NIT) and numero and not numero.isdigit():
        raise ValueError(f"El número de {tipo} solo puede tener dígitos")


# --- Propietarios ---------------------------------------------------------------------------


class PropietarioCrear(Entrada):
    nombre: _texto(1, 150)
    tipo_documento: TipoDocumento
    numero_documento: NumeroDocumento
    telefono: Telefono | None = None
    correo: Correo | None = None
    direccion: _texto(1, 200) | None = None
    notas: _texto(1, 1000) | None = None

    @model_validator(mode="after")
    def _documento(self) -> "PropietarioCrear":
        _documento_numerico(self.tipo_documento, self.numero_documento)
        return self


class PropietarioEditar(Entrada):
    obligatorios = ("nombre", "tipo_documento", "numero_documento")

    nombre: _texto(1, 150) | None = None
    tipo_documento: TipoDocumento | None = None
    numero_documento: NumeroDocumento | None = None
    telefono: Telefono | None = None
    correo: Correo | None = None
    direccion: _texto(1, 200) | None = None
    notas: _texto(1, 1000) | None = None


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
    direccion: _texto(1, 200)
    area_m2: Area | None = None
    descripcion: _texto(1, 1000) | None = None


class ApartaestudioEditar(Entrada):
    obligatorios = ("codigo", "propietario_id", "direccion")

    codigo: Codigo | None = None
    propietario_id: int | None = None
    direccion: _texto(1, 200) | None = None
    area_m2: Area | None = None
    descripcion: _texto(1, 1000) | None = None


class CambioMantenimiento(Entrada):
    activo: bool
    motivo: _texto(3, 300)


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
