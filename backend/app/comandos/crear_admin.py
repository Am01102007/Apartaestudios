"""Crea un administrador desde la consola. Sirve para el primer ingreso y como recuperación.

Uso:
    uv run python -m app.comandos.crear_admin --usuario admin --nombre "Nombre Apellido"

La contraseña se pide por teclado sin mostrarse. Para automatizar, puede pasarse en la
variable de entorno APP_CONTRASENA_ADMIN (nunca como argumento, porque quedaría en el
historial de la consola).
"""

import argparse
import getpass
import os
import sys

from pydantic import ValidationError

from app.comandos import abrir_sesion
from app.core.errores import ErrorAplicacion
from app.modulos.usuarios import servicio
from app.modulos.usuarios.esquemas import UsuarioCrear
from app.modulos.usuarios.modelos import Rol


def _leer_contrasena() -> str:
    if contrasena := os.environ.get("APP_CONTRASENA_ADMIN"):
        return contrasena
    primera = getpass.getpass("Contraseña (mínimo 10 caracteres): ")
    if primera != getpass.getpass("Repite la contraseña: "):
        raise SystemExit("Las contraseñas no coinciden.")
    return primera


def main(argumentos: list[str] | None = None) -> int:
    lector = argparse.ArgumentParser(description="Crea un usuario administrador.")
    lector.add_argument("--usuario", required=True, help="Nombre de usuario para ingresar")
    lector.add_argument("--nombre", required=True, help="Nombre completo")
    lector.add_argument("--correo", default=None, help="Correo de contacto (opcional)")
    opciones = lector.parse_args(argumentos)

    try:
        datos = UsuarioCrear(
            nombre_usuario=opciones.usuario,
            nombre=opciones.nombre,
            correo=opciones.correo,
            rol=Rol.ADMINISTRADOR,
            contrasena_temporal=_leer_contrasena(),
        )
    except ValidationError as error:
        for detalle in error.errors():
            print(f"Dato inválido en {detalle['loc'][0]}: {detalle['msg']}", file=sys.stderr)
        return 1

    with abrir_sesion() as sesion:
        try:
            usuario = servicio.crear(
                sesion, datos, actor_id=None, ip="consola", debe_cambiar_contrasena=False
            )
            sesion.commit()
        except ErrorAplicacion as error:
            print(error.mensaje, file=sys.stderr)
            return 1
        print(f"Administrador «{usuario.nombre_usuario}» creado con id {usuario.id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
