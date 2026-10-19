"""Normalización de documentos y códigos (RP-02, RP-03). Funciones puras, sin base de datos."""

import re

_SEPARADORES_DOCUMENTO = re.compile(r"[.\s-]")
_ESPACIOS = re.compile(r"\s+")


def normalizar_documento(valor: str) -> str:
    """`1.234.567` → `1234567`; `ab-12 3` → `AB123`."""
    return _SEPARADORES_DOCUMENTO.sub("", valor).upper()


def normalizar_codigo(valor: str) -> str:
    """`  a-302 ` → `A-302`; `torre  b 2` → `TORRE B 2`."""
    return _ESPACIOS.sub(" ", valor.strip()).upper()


def patron_busqueda(texto: str) -> str:
    """Patrón ILIKE que busca el texto literal (sin que % o _ actúen como comodines)."""
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"
