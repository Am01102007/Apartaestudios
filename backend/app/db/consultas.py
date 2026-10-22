"""Ayudas de consulta compartidas por los repositorios."""


def patron_busqueda(texto: str) -> str:
    """Patrón ILIKE que busca el texto literal (sin que % o _ actúen como comodines).

    Úsalo con `escape="\\\\"`: `columna.ilike(patron_busqueda(t), escape="\\\\")`.
    """
    escapado = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"
