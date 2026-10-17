"""Endpoints de sesión: /auth/*."""

from datetime import timedelta

from fastapi import APIRouter, Request, Response, status

from app.api.dependencias import BD, IP, Config, Reloj
from app.core.errores import DemasiadasSolicitudes
from app.modulos.usuarios import autenticacion
from app.modulos.usuarios.dependencias import (
    COOKIE_CSRF,
    COOKIE_SESION,
    SesionConCambioPendiente,
)
from app.modulos.usuarios.esquemas import CambioContrasena, CredencialesIngreso, UsuarioActual

router = APIRouter(prefix="/auth", tags=["sesión"])


def _poner_cookies(respuesta: Response, ingreso: autenticacion.Ingreso, config) -> None:
    duracion = int(timedelta(hours=config.horas_maximas_sesion).total_seconds())
    respuesta.set_cookie(
        COOKIE_SESION,
        ingreso.jwt,
        max_age=duracion,
        path="/api",
        httponly=True,
        secure=config.cookie_segura,
        samesite="strict",
    )
    # Legible por el frontend para enviarlo en la cabecera X-CSRF-Token.
    respuesta.set_cookie(
        COOKIE_CSRF,
        ingreso.token_csrf,
        max_age=duracion,
        path="/",
        httponly=False,
        secure=config.cookie_segura,
        samesite="strict",
    )


def _borrar_cookies(respuesta: Response, config) -> None:
    respuesta.delete_cookie(
        COOKIE_SESION, path="/api", httponly=True, secure=config.cookie_segura, samesite="strict"
    )
    respuesta.delete_cookie(COOKIE_CSRF, path="/", secure=config.cookie_segura, samesite="strict")


@router.post("/login", response_model=UsuarioActual, summary="Iniciar sesión")
def iniciar_sesion(
    credenciales: CredencialesIngreso,
    request: Request,
    respuesta: Response,
    bd: BD,
    config: Config,
    reloj: Reloj,
    ip: IP,
):
    ahora = reloj()
    if not request.app.state.limite_ingreso.permitir(ip or "desconocida", ahora):
        raise DemasiadasSolicitudes("Demasiados intentos de ingreso. Espera un minuto.")
    try:
        ingreso = autenticacion.iniciar_sesion(
            bd,
            credenciales.nombre_usuario,
            credenciales.contrasena,
            config=config,
            ahora=ahora,
            ip=ip,
            agente_usuario=request.headers.get("user-agent"),
        )
    except autenticacion.IngresoRechazado:
        bd.commit()  # se guardan el intento fallido, el bloqueo y su auditoría
        raise
    bd.commit()
    _poner_cookies(respuesta, ingreso, config)
    return ingreso.usuario


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Cerrar sesión")
def cerrar_sesion(
    sesion: SesionConCambioPendiente, bd: BD, config: Config, reloj: Reloj, ip: IP
) -> Response:
    autenticacion.cerrar_sesion(bd, sesion, ahora=reloj(), ip=ip)
    bd.commit()
    respuesta = Response(status_code=status.HTTP_204_NO_CONTENT)
    _borrar_cookies(respuesta, config)
    return respuesta


@router.get("/yo", response_model=UsuarioActual, summary="Usuario de la sesión actual")
def yo(sesion: SesionConCambioPendiente):
    return sesion.usuario


@router.post(
    "/cambiar-contrasena",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cambiar la propia contraseña",
)
def cambiar_contrasena(
    datos: CambioContrasena, sesion: SesionConCambioPendiente, bd: BD, reloj: Reloj, ip: IP
) -> None:
    autenticacion.cambiar_contrasena(
        bd, sesion, datos.contrasena_actual, datos.contrasena_nueva, ahora=reloj(), ip=ip
    )
    bd.commit()
