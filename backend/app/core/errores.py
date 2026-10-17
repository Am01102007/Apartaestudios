"""Manejo centralizado de errores (RNF-04).

Toda respuesta de error tiene el mismo formato:

    {"error": {"codigo": "...", "mensaje": "...", "detalles": [...]}}

Los servicios lanzan las excepciones de este módulo; nunca construyen respuestas HTTP.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorAplicacion(Exception):
    """Error esperado de la aplicación, con código estable para el frontend."""

    estado_http = status.HTTP_400_BAD_REQUEST
    codigo = "error"

    def __init__(self, mensaje: str, detalles: list[Any] | None = None, codigo: str | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalles = detalles or []
        if codigo:
            self.codigo = codigo


class NoAutenticado(ErrorAplicacion):
    estado_http = status.HTTP_401_UNAUTHORIZED
    codigo = "no_autenticado"


class SinPermiso(ErrorAplicacion):
    estado_http = status.HTTP_403_FORBIDDEN
    codigo = "sin_permiso"


class NoEncontrado(ErrorAplicacion):
    estado_http = status.HTTP_404_NOT_FOUND
    codigo = "no_encontrado"


class DatosInvalidos(ErrorAplicacion):
    """Datos con formato correcto que no cumplen una validación del servidor."""

    estado_http = status.HTTP_422_UNPROCESSABLE_CONTENT
    codigo = "datos_invalidos"


class DemasiadasSolicitudes(ErrorAplicacion):
    estado_http = status.HTTP_429_TOO_MANY_REQUESTS
    codigo = "demasiadas_solicitudes"


class ReglaDeNegocio(ErrorAplicacion):
    """Una regla de negocio impide la operación (por ejemplo, contrato superpuesto)."""

    estado_http = status.HTTP_409_CONFLICT
    codigo = "regla_de_negocio"


def respuesta_error(
    estado_http: int, codigo: str, mensaje: str, detalles: list[Any] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=estado_http,
        content={"error": {"codigo": codigo, "mensaje": mensaje, "detalles": detalles or []}},
    )


_MENSAJES_HTTP = {
    401: ("no_autenticado", "Debes iniciar sesión."),
    403: ("sin_permiso", "No tienes permiso para esta operación."),
    404: ("no_encontrado", "El recurso no existe."),
    405: ("metodo_no_permitido", "Método no permitido."),
}


async def _manejar_error_aplicacion(_: Request, exc: ErrorAplicacion) -> JSONResponse:
    return respuesta_error(exc.estado_http, exc.codigo, exc.mensaje, exc.detalles)


async def _manejar_validacion(_: Request, exc: RequestValidationError) -> JSONResponse:
    detalles = [
        {
            "campo": ".".join(str(parte) for parte in error["loc"] if parte != "body"),
            "mensaje": error["msg"],
            "tipo": error["type"],
        }
        for error in exc.errors()
    ]
    return respuesta_error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "datos_invalidos",
        "Los datos enviados no son válidos.",
        detalles,
    )


async def _manejar_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    codigo, mensaje = _MENSAJES_HTTP.get(exc.status_code, ("error_http", str(exc.detail)))
    return respuesta_error(exc.status_code, codigo, mensaje)


# Conflictos de concurrencia de PostgreSQL: la operación no se aplicó y puede reintentarse.
SQLSTATE_REINTENTABLES = {
    "40P01": "bloqueo mutuo (deadlock)",
    "40001": "fallo de serialización",
}


async def _manejar_operacional(request: Request, exc: OperationalError) -> JSONResponse:
    sqlstate = getattr(exc.orig, "sqlstate", None)
    if sqlstate in SQLSTATE_REINTENTABLES:
        logger.warning(
            "Conflicto de concurrencia (%s) en %s %s",
            SQLSTATE_REINTENTABLES[sqlstate],
            request.method,
            request.url.path,
        )
        return respuesta_error(
            status.HTTP_409_CONFLICT,
            "conflicto_concurrente",
            "Otra operación modificó los mismos datos al mismo tiempo. Intenta de nuevo.",
        )
    return await _manejar_inesperado(request, exc)


async def _manejar_inesperado(request: Request, exc: Exception) -> JSONResponse:
    # El detalle va al registro del servidor, nunca al cliente.
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return respuesta_error(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "error_interno", "Ocurrió un error inesperado."
    )


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(ErrorAplicacion, _manejar_error_aplicacion)
    app.add_exception_handler(RequestValidationError, _manejar_validacion)
    app.add_exception_handler(StarletteHTTPException, _manejar_http)
    app.add_exception_handler(OperationalError, _manejar_operacional)
    app.add_exception_handler(Exception, _manejar_inesperado)
