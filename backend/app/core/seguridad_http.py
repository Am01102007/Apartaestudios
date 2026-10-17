"""Cabeceras de seguridad que se añaden a todas las respuestas de la API."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CABECERAS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}

# La documentación interactiva carga recursos externos; su política se relaja solo ahí.
RUTAS_DOCUMENTACION = ("/api/docs", "/api/openapi.json")


class CabecerasSeguridad(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        respuesta = await call_next(request)
        for nombre, valor in CABECERAS.items():
            if nombre == "Content-Security-Policy" and request.url.path.startswith(
                RUTAS_DOCUMENTACION
            ):
                continue
            respuesta.headers.setdefault(nombre, valor)
        return respuesta
