"""Ayudas para las pruebas de integración del módulo de usuarios."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modulos.usuarios import servicio
from app.modulos.usuarios.esquemas import UsuarioCrear
from app.modulos.usuarios.modelos import Rol, Usuario

CONTRASENA = "contrasena-segura-1"


def crear_usuario(
    sesion: Session,
    nombre_usuario: str,
    rol: Rol = Rol.EMPLEADO,
    contrasena: str = CONTRASENA,
    debe_cambiar: bool = False,
) -> Usuario:
    datos = UsuarioCrear(
        nombre_usuario=nombre_usuario,
        nombre=nombre_usuario.title(),
        rol=rol,
        contrasena_temporal=contrasena,
    )
    return servicio.crear(
        sesion, datos, actor_id=None, ip=None, debe_cambiar_contrasena=debe_cambiar
    )


def ingresar(cliente: TestClient, nombre_usuario: str, contrasena: str = CONTRASENA):
    """Inicia sesión y deja el token CSRF en las cabeceras del cliente, como haría el frontend."""
    respuesta = cliente.post(
        "/api/v1/auth/login", json={"nombre_usuario": nombre_usuario, "contrasena": contrasena}
    )
    if respuesta.status_code == 200:
        cliente.headers["X-CSRF-Token"] = respuesta.cookies["csrf_token"]
    return respuesta
