"""Dependencias de autenticación y autorización para todos los routers (RNF-03).

- `SesionActual`: exige sesión válida, token CSRF en métodos que modifican datos y que el
  usuario no tenga pendiente el cambio de contraseña.
- `SesionConCambioPendiente`: igual, pero permite entrar a quien debe cambiar la contraseña;
  solo la usan /auth/yo, /auth/logout y /auth/cambiar-contrasena.
- `requiere_rol(...)`: además, exige uno de los roles indicados; `solo_administrador` es la
  instancia para el administrador.
"""

from typing import Annotated

from fastapi import Depends, Header, Request

from app.api.dependencias import BD, Config, Reloj
from app.core.errores import SinPermiso
from app.modulos.usuarios.autenticacion import csrf_valido, validar_sesion
from app.modulos.usuarios.modelos import Rol, Sesion

COOKIE_SESION = "sesion"
COOKIE_CSRF = "csrf_token"
CABECERA_CSRF = "X-CSRF-Token"
METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}


def _sesion_con_cambio_pendiente(
    request: Request,
    bd: BD,
    config: Config,
    reloj: Reloj,
    # Declarada para que la documentación /api/docs permita escribirla al probar.
    token_csrf: Annotated[
        str | None,
        Header(
            alias=CABECERA_CSRF,
            description="Valor de la cookie csrf_token. Obligatorio en POST, PATCH y DELETE.",
        ),
    ] = None,
) -> Sesion:
    sesion = validar_sesion(bd, request.cookies.get(COOKIE_SESION), config=config, ahora=reloj())
    if request.method not in METODOS_SEGUROS and not csrf_valido(sesion, token_csrf):
        raise SinPermiso(
            "Falta el token de seguridad o no es válido. Recarga la página.",
            codigo="csrf_invalido",
        )
    return sesion


SesionConCambioPendiente = Annotated[Sesion, Depends(_sesion_con_cambio_pendiente)]


def _sesion_actual(sesion: SesionConCambioPendiente) -> Sesion:
    if sesion.usuario.debe_cambiar_contrasena:
        raise SinPermiso(
            "Debes cambiar tu contraseña antes de continuar.", codigo="debe_cambiar_contrasena"
        )
    return sesion


SesionActual = Annotated[Sesion, Depends(_sesion_actual)]
# Para `dependencies=[Depends(requiere_sesion)]` en routers que consultan ambos roles.
requiere_sesion = _sesion_actual


def requiere_rol(*roles: Rol):
    def _verificar(sesion: SesionActual) -> Sesion:
        if sesion.usuario.rol not in roles:
            raise SinPermiso("No tienes permiso para esta operación.")
        return sesion

    return _verificar


# Una sola instancia: FastAPI ejecuta una vez por petición cada dependencia, aunque se use en
# el router y en el endpoint.
solo_administrador = requiere_rol(Rol.ADMINISTRADOR)
SesionAdministrador = Annotated[Sesion, Depends(solo_administrador)]
