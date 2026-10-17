"""Registro de auditoría inmodificable y su consulta (U-17, U-18)."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.modulos.auditoria import servicio as auditoria
from app.modulos.usuarios.modelos import Rol
from tests.integration.ayudas import crear_usuario, ingresar

pytestmark = pytest.mark.integracion


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE auditoria SET accion = 'alterada'",
        "DELETE FROM auditoria",
        "TRUNCATE auditoria",
    ],
)
def test_u18_la_base_de_datos_impide_modificar_la_auditoria(sesion_bd, sentencia):
    auditoria.registrar(sesion_bd, accion="prueba", entidad="prueba")
    sesion_bd.flush()
    with pytest.raises(DBAPIError, match="no se puede modificar"):
        sesion_bd.execute(text(sentencia))
    sesion_bd.rollback()


def test_consulta_con_filtros_y_paginacion(nuevo_cliente, sesion_bd, reloj):
    admin = crear_usuario(sesion_bd, "admin", Rol.ADMINISTRADOR)
    cliente = nuevo_cliente()
    ingresar(cliente, "admin")
    ingresar(nuevo_cliente(), "admin", "mala-contrasena")

    r = cliente.get("/api/v1/auditoria", params={"accion": "sesion.ingreso"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] == 1
    assert cuerpo["registros"][0]["usuario_id"] == admin.id

    r = cliente.get("/api/v1/auditoria", params={"entidad": "usuario", "limite": 1})
    assert len(r.json()["registros"]) == 1
    assert r.json()["total"] >= 3

    assert cliente.get("/api/v1/auditoria", params={"limite": 500}).status_code == 422


def test_filtro_de_fechas_usa_dias_de_bogota(sesion_bd):
    from datetime import UTC, date, datetime

    # 2026-10-18 03:00 UTC es todavía el 17 de octubre en Bogotá.
    auditoria.registrar(
        sesion_bd,
        accion="prueba.fecha",
        entidad="prueba",
        momento=datetime(2026, 10, 18, 3, 0, tzinfo=UTC),
    )
    sesion_bd.flush()
    comunes = dict(usuario_id=None, accion="prueba.fecha", entidad=None, entidad_id=None)
    _, el_17 = auditoria.consultar(
        sesion_bd,
        **comunes,
        desde=date(2026, 10, 17),
        hasta=date(2026, 10, 17),
        limite=10,
        desplazamiento=0,
    )
    _, el_18 = auditoria.consultar(
        sesion_bd,
        **comunes,
        desde=date(2026, 10, 18),
        hasta=date(2026, 10, 18),
        limite=10,
        desplazamiento=0,
    )
    assert (el_17, el_18) == (1, 0)
