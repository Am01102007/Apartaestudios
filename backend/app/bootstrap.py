"""Crea el primer administrador si todavía no existe. Se puede ejecutar en cada despliegue.

Uso:  python -m app.bootstrap

Lee APP_ADMIN_USUARIO, APP_ADMIN_NOMBRE y APP_CONTRASENA_ADMIN del entorno. Si falta el
usuario o la contraseña, no hace nada: el despliegue continúa y el administrador puede
crearse después con `python -m app.comandos.crear_admin`.
"""

import os
import sys

from pydantic import ValidationError

from app.comandos import abrir_sesion
from app.core.config import obtener_configuracion
from app.core.errores import ErrorAplicacion
from app.modulos.usuarios import repositorio, servicio
from app.modulos.usuarios.esquemas import UsuarioCrear
from app.modulos.usuarios.modelos import Rol


def main() -> int:
    configuracion = obtener_configuracion()
    usuario = configuracion.admin_usuario
    contrasena = os.environ.get("APP_CONTRASENA_ADMIN")
    if not usuario or not contrasena:
        print("Bootstrap omitido: faltan APP_ADMIN_USUARIO o APP_CONTRASENA_ADMIN.")
        return 0

    try:
        datos = UsuarioCrear(
            nombre_usuario=usuario,
            nombre=configuracion.admin_nombre,
            rol=Rol.ADMINISTRADOR,
            contrasena_temporal=contrasena,
        )
    except ValidationError as error:
        for detalle in error.errors():
            print(f"Dato inválido en {detalle['loc'][0]}: {detalle['msg']}", file=sys.stderr)
        return 1

    with abrir_sesion() as sesion:
        if repositorio.existe_nombre_usuario(sesion, datos.nombre_usuario):
            print(f"Bootstrap: el usuario «{datos.nombre_usuario}» ya existe; no se modifica.")
            return 0
        try:
            creado = servicio.crear(
                sesion, datos, actor_id=None, ip="bootstrap", debe_cambiar_contrasena=False
            )
            sesion.commit()
        except ErrorAplicacion as error:
            print(error.mensaje, file=sys.stderr)
            return 1
        print(f"Bootstrap: administrador «{creado.nombre_usuario}» creado con id {creado.id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
