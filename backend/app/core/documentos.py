"""Documentos de identidad, compartidos por propietarios, residentes y bloqueos (RP-02).

Todos los dominios usan exactamente la misma normalización, para que un documento escrito
`1.234.567` en un lugar y `1234567` en otro sea siempre el mismo.
"""

import re
from enum import StrEnum

from sqlalchemy import Enum

_SEPARADORES = re.compile(r"[.\s-]")


class TipoDocumento(StrEnum):
    CC = "CC"
    CE = "CE"
    NIT = "NIT"
    PA = "PA"
    PPT = "PPT"


SQL_TIPO_VALIDO = "tipo_documento IN ('CC', 'CE', 'NIT', 'PA', 'PPT')"
SQL_NUMERO_NORMALIZADO = "numero_documento ~ '^[A-Z0-9]{3,20}$'"
TIPOS_SOLO_DIGITOS = (TipoDocumento.CC, TipoDocumento.NIT)


def columna_tipo() -> Enum:
    return Enum(TipoDocumento, native_enum=False, create_constraint=False, length=5)


def normalizar_documento(valor: str) -> str:
    """`1.234.567` → `1234567`; `ab-12 3` → `AB123`."""
    return _SEPARADORES.sub("", valor).upper()


def error_documento(tipo: TipoDocumento | None, numero: str | None) -> str | None:
    """Mensaje si el número no corresponde al tipo (cédulas y NIT solo llevan dígitos)."""
    if tipo in TIPOS_SOLO_DIGITOS and numero and not numero.isdigit():
        return f"El número de {tipo} solo puede tener dígitos"
    return None
