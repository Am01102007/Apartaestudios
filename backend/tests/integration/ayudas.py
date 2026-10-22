"""Ayudas comunes de las pruebas de integración."""

import threading

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
    usuario = servicio.crear(
        sesion, datos, actor_id=None, ip=None, debe_cambiar_contrasena=debe_cambiar
    )
    sesion.commit()
    return usuario


def ingresar(cliente: TestClient, nombre_usuario: str, contrasena: str = CONTRASENA):
    """Inicia sesión y deja el token CSRF en las cabeceras del cliente, como haría el frontend."""
    respuesta = cliente.post(
        "/api/v1/auth/login", json={"nombre_usuario": nombre_usuario, "contrasena": contrasena}
    )
    if respuesta.status_code == 200:
        cliente.headers["X-CSRF-Token"] = respuesta.cookies["csrf_token"]
    return respuesta


def en_paralelo(*tareas) -> list[object]:
    """Ejecuta cada tarea en su hilo y devuelve "ok" o la excepción de cada una."""
    resultados: list[object] = [None] * len(tareas)

    def correr(i, tarea):
        try:
            tarea()
            resultados[i] = "ok"
        except Exception as error:  # noqa: BLE001 - se examina en cada prueba
            resultados[i] = error

    hilos = [threading.Thread(target=correr, args=(i, t)) for i, t in enumerate(tareas)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=20)
    assert not any(h.is_alive() for h in hilos), "una petición quedó esperando (bloqueo mutuo)"
    return resultados
