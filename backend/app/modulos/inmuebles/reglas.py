"""Normalización de códigos (RP-03). Funciones puras, sin base de datos.

La de documentos está en app.core.documentos, porque la comparten varios dominios.
"""

import re

_ESPACIOS = re.compile(r"\s+")


def normalizar_codigo(valor: str) -> str:
    """`  a-302 ` → `A-302`; `torre  b 2` → `TORRE B 2`."""
    return _ESPACIOS.sub(" ", valor.strip()).upper()
