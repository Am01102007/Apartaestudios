"""Recorre TODOS los endpoints con cada rol (RNF-03, CA-16, U-11).

La tabla PERMISOS es la especificación: cada endpoint nuevo debe agregarse aquí, o la
prueba `test_todos_los_endpoints_estan_clasificados` falla.
"""

import re

import pytest

from app.modulos.usuarios.modelos import Rol
from tests.integration.ayudas import crear_usuario, ingresar

pytestmark = pytest.mark.integracion

PUBLICO, AMBOS, ADMIN = "publico", "ambos", "admin"

PERMISOS = {
    ("GET", "/api/v1/salud"): PUBLICO,
    ("GET", "/health/live"): PUBLICO,
    ("GET", "/health/ready"): PUBLICO,
    ("POST", "/api/v1/auth/login"): PUBLICO,
    ("POST", "/api/v1/auth/logout"): AMBOS,
    ("GET", "/api/v1/auth/yo"): AMBOS,
    ("POST", "/api/v1/auth/cambiar-contrasena"): AMBOS,
    ("GET", "/api/v1/usuarios"): ADMIN,
    ("POST", "/api/v1/usuarios"): ADMIN,
    ("GET", "/api/v1/usuarios/{usuario_id}"): ADMIN,
    ("PATCH", "/api/v1/usuarios/{usuario_id}"): ADMIN,
    ("POST", "/api/v1/usuarios/{usuario_id}/desactivar"): ADMIN,
    ("POST", "/api/v1/usuarios/{usuario_id}/activar"): ADMIN,
    ("POST", "/api/v1/usuarios/{usuario_id}/restablecer-contrasena"): ADMIN,
    ("GET", "/api/v1/auditoria"): ADMIN,
    ("GET", "/api/v1/propietarios"): AMBOS,
    ("POST", "/api/v1/propietarios"): ADMIN,
    ("GET", "/api/v1/propietarios/{propietario_id}"): AMBOS,
    ("PATCH", "/api/v1/propietarios/{propietario_id}"): ADMIN,
    ("POST", "/api/v1/propietarios/{propietario_id}/desactivar"): ADMIN,
    ("POST", "/api/v1/propietarios/{propietario_id}/activar"): ADMIN,
    ("GET", "/api/v1/apartaestudios"): AMBOS,
    ("POST", "/api/v1/apartaestudios"): ADMIN,
    ("GET", "/api/v1/apartaestudios/{apartaestudio_id}"): AMBOS,
    ("PATCH", "/api/v1/apartaestudios/{apartaestudio_id}"): ADMIN,
    ("POST", "/api/v1/apartaestudios/{apartaestudio_id}/mantenimiento"): ADMIN,
    ("POST", "/api/v1/apartaestudios/{apartaestudio_id}/desactivar"): ADMIN,
    ("POST", "/api/v1/apartaestudios/{apartaestudio_id}/activar"): ADMIN,
    ("GET", "/api/v1/residentes"): AMBOS,
    ("POST", "/api/v1/residentes"): ADMIN,
    ("GET", "/api/v1/residentes/{residente_id}"): AMBOS,
    ("PATCH", "/api/v1/residentes/{residente_id}"): ADMIN,
    ("GET", "/api/v1/bloqueos"): AMBOS,
    ("GET", "/api/v1/bloqueos/verificar"): AMBOS,
    ("POST", "/api/v1/bloqueos"): ADMIN,
    ("POST", "/api/v1/bloqueos/{bloqueo_id}/levantar"): ADMIN,
    ("GET", "/api/v1/contratos"): AMBOS,
    ("POST", "/api/v1/contratos"): AMBOS,
    ("GET", "/api/v1/contratos/{contrato_id}"): AMBOS,
    ("PATCH", "/api/v1/contratos/{contrato_id}"): AMBOS,
    ("POST", "/api/v1/contratos/{contrato_id}/prorrogar"): AMBOS,
    ("POST", "/api/v1/contratos/{contrato_id}/renovar"): AMBOS,
    ("POST", "/api/v1/contratos/{contrato_id}/terminar"): AMBOS,
    ("POST", "/api/v1/contratos/{contrato_id}/anular"): ADMIN,
    ("GET", "/api/v1/contratos/{contrato_id}/historial"): AMBOS,
    ("GET", "/api/v1/apartaestudios/{apartaestudio_id}/contratos"): AMBOS,
    ("GET", "/api/v1/residentes/{residente_id}/contratos"): AMBOS,
}


def endpoints(app):
    for ruta, operaciones in app.openapi()["paths"].items():
        for metodo in operaciones:
            yield metodo.upper(), ruta


def test_todos_los_endpoints_estan_clasificados(app):
    assert set(endpoints(app)) == set(PERMISOS)


def _llamar(cliente, metodo, ruta):
    return cliente.request(metodo, re.sub(r"\{\w+_id\}", "999999", ruta), json={})


def test_sin_sesion_solo_responden_los_publicos(app, cliente_bd):
    for (metodo, ruta), nivel in PERMISOS.items():
        r = _llamar(cliente_bd, metodo, ruta)
        if nivel == PUBLICO:
            assert r.status_code != 401, (metodo, ruta)
        else:
            assert r.status_code == 401, (metodo, ruta, r.status_code)


def test_u11_empleado_recibe_403_en_todo_endpoint_de_administrador(nuevo_cliente, sesion_bd):
    crear_usuario(sesion_bd, "empleado")
    cliente = nuevo_cliente()
    ingresar(cliente, "empleado")
    for (metodo, ruta), nivel in PERMISOS.items():
        if ruta.endswith(("/logout", "/login")):
            continue  # cerrarían la sesión o abrirían otra
        r = _llamar(cliente, metodo, ruta)
        if nivel == ADMIN:
            assert r.status_code == 403, (metodo, ruta, r.status_code)
            assert r.json()["error"]["codigo"] == "sin_permiso"
        else:
            assert r.status_code not in (401, 403), (metodo, ruta, r.status_code)


def test_administrador_accede_a_todos_los_endpoints(nuevo_cliente, sesion_bd):
    crear_usuario(sesion_bd, "admin", Rol.ADMINISTRADOR)
    cliente = nuevo_cliente()
    ingresar(cliente, "admin")
    for (metodo, ruta), _ in PERMISOS.items():
        if ruta.endswith(("/logout", "/login")):
            continue
        r = _llamar(cliente, metodo, ruta)
        assert r.status_code not in (401, 403), (metodo, ruta, r.status_code)
