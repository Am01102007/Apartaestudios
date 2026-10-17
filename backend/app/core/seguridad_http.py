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


# En producción el sitio solo se sirve por HTTPS (RNF-05): el navegador no volverá a usar HTTP.
HSTS = "max-age=31536000; includeSubDomains"


class CabecerasSeguridad(BaseHTTPMiddleware):
    def __init__(self, app, hsts: bool = False):
        super().__init__(app)
        self.hsts = hsts

    async def dispatch(self, request: Request, call_next) -> Response:
        respuesta = await call_next(request)
        if self.hsts:
            respuesta.headers.setdefault("Strict-Transport-Security", HSTS)
        for nombre, valor in CABECERAS.items():
            if nombre == "Content-Security-Policy" and request.url.path.startswith(
                RUTAS_DOCUMENTACION
            ):
                continue
            respuesta.headers.setdefault(nombre, valor)
        return respuesta
