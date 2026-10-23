from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.entradas import Entrada, texto
from app.modulos.contratos.estados import EstadoContrato

Canon = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=0)]
PorcentajeIncremento = Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]


def _terminacion_posterior(inicio: date | None, terminacion: date | None) -> None:
    if inicio is not None and terminacion is not None and terminacion <= inicio:
        raise ValueError("La fecha de terminación debe ser posterior a la de inicio")


class ContratoCrear(Entrada):
    apartaestudio_id: int
    residente_id: int
    fecha_inicio: date
    fecha_terminacion: date
    canon_inicial: Canon
    porcentaje_incremento: PorcentajeIncremento
    notas: texto(1, 1000) | None = None

    @model_validator(mode="after")
    def _fechas(self) -> "ContratoCrear":
        _terminacion_posterior(self.fecha_inicio, self.fecha_terminacion)
        return self


class ContratoEditar(Entrada):
    obligatorios = ("fecha_inicio", "fecha_terminacion", "canon_inicial", "porcentaje_incremento")

    fecha_inicio: date | None = None
    fecha_terminacion: date | None = None
    canon_inicial: Canon | None = None
    porcentaje_incremento: PorcentajeIncremento | None = None
    notas: texto(1, 1000) | None = None


class ProrrogaCrear(Entrada):
    fecha_terminacion: date


class RenovacionCrear(Entrada):
    """El inicio lo calcula el sistema (D-2). El canon por defecto es el vigente."""

    fecha_terminacion: date
    canon_inicial: Canon | None = None
    porcentaje_incremento: PorcentajeIncremento
    notas: texto(1, 1000) | None = None


class TerminacionCrear(Entrada):
    fecha_aviso: date
    fecha_entrega: date
    motivo: texto(3, 500)


class Anulacion(Entrada):
    motivo: texto(3, 500)


class Referencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class ApartaestudioReferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    propietario_id: int


class ResidenteReferencia(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    tipo_documento: str
    numero_documento: str


class ContratoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: EstadoContrato
    apartaestudio: ApartaestudioReferencia
    residente: ResidenteReferencia
    fecha_inicio: date
    fecha_terminacion: date
    canon_inicial: Decimal
    canon_vigente: Decimal
    porcentaje_incremento: Decimal
    notas: str | None
    contrato_anterior_id: int | None
    contrato_siguiente_id: int | None
    fecha_aviso: date | None
    fecha_entrega: date | None
    motivo_terminacion: str | None
    anulado_en: datetime | None
    motivo_anulacion: str | None
    creado_por: Referencia
    creado_en: datetime


class ProrrogaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    terminacion_anterior: date
    terminacion_nueva: date
    registrada_por: Referencia
    registrada_en: datetime


class ContratoDetalle(ContratoSalida):
    dia_corte: int
    proximo_corte: date | None
    proximo_aniversario: date | None
    prorrogas: list[ProrrogaSalida]


class Cambio(BaseModel):
    """Un registro del historial (RF-10): sale de la auditoría."""

    momento: datetime
    accion: str
    usuario: Referencia | None
    valor_anterior: dict[str, Any] | None
    valor_nuevo: dict[str, Any] | None
