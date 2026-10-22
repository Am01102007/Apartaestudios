"""Fijaciones de las pruebas de integración: clientes con sesión de cada rol.

Un archivo de pruebas puede definir las suyas con el mismo nombre; en ese caso usa las propias.
"""

import pytest

from app.modulos.usuarios.modelos import Rol
from tests.integration.ayudas import crear_usuario, ingresar


@pytest.fixture
def cliente_admin(nuevo_cliente, sesion_bd):
    crear_usuario(sesion_bd, "admin", Rol.ADMINISTRADOR)
    cliente = nuevo_cliente()
    assert ingresar(cliente, "admin").status_code == 200
    return cliente


@pytest.fixture
def cliente_empleado(nuevo_cliente, sesion_bd):
    crear_usuario(sesion_bd, "empleado")
    cliente = nuevo_cliente()
    assert ingresar(cliente, "empleado").status_code == 200
    return cliente
