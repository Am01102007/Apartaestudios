"""Residentes (R-01 a R-04, R-12; RF-06)."""

import pytest
from sqlalchemy import select

from app.modulos.auditoria.modelos import RegistroAuditoria
from tests.integration.ayudas_personas import (
    crear_bloqueo,
    crear_residente,
    datos_residente,
)

pytestmark = pytest.mark.integracion
URL = "/api/v1/residentes"


def auditorias(sesion_bd, entidad_id):
    return list(
        sesion_bd.scalars(
            select(RegistroAuditoria)
            .where(
                RegistroAuditoria.entidad == "residente",
                RegistroAuditoria.entidad_id == str(entidad_id),
            )
            .order_by(RegistroAuditoria.id)
        )
    )


def test_r01_el_administrador_registra_y_el_empleado_consulta(cliente_admin, cliente_empleado):
    residente = crear_residente(cliente_admin)
    assert residente["numero_documento"] == "1020304"
    assert residente["correo"] == "carlos@correo.com"

    r = cliente_empleado.post(URL, json=datos_residente(numero_documento="999999"))
    assert r.status_code == 403
    assert cliente_empleado.get(f"{URL}/{residente['id']}").status_code == 200


@pytest.mark.parametrize(
    "cambios",
    [
        {"telefono": None},
        {"numero_documento": "10203AB"},  # CC solo dígitos
        {"contacto_emergencia_nombre": "Ana Pérez"},  # falta el teléfono
        {"estado": "activo"},  # campo desconocido
    ],
)
def test_r01_datos_invalidos_se_rechazan(cliente_admin, cambios):
    r = cliente_admin.post(URL, json=datos_residente(**cambios))
    assert r.status_code == 422


def test_contacto_de_emergencia_completo(cliente_admin):
    residente = crear_residente(
        cliente_admin,
        contacto_emergencia_nombre="Ana Pérez",
        contacto_emergencia_telefono="320 111 2233",
    )
    r = cliente_admin.patch(f"{URL}/{residente['id']}", json={"contacto_emergencia_nombre": None})
    assert r.status_code == 422
    r = cliente_admin.patch(
        f"{URL}/{residente['id']}",
        json={"contacto_emergencia_nombre": None, "contacto_emergencia_telefono": None},
    )
    assert r.status_code == 200
    assert r.json()["contacto_emergencia_nombre"] is None


@pytest.mark.parametrize("variante", ["1020304", "1 020 304", "1-020-304"])
def test_r02_documento_duplicado(cliente_admin, variante):
    crear_residente(cliente_admin)
    r = cliente_admin.post(URL, json=datos_residente(numero_documento=variante))
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "documento_duplicado"


def test_r02_editar_hacia_un_documento_existente(cliente_admin):
    crear_residente(cliente_admin)
    otro = crear_residente(cliente_admin, numero_documento="5555555")
    r = cliente_admin.patch(f"{URL}/{otro['id']}", json={"numero_documento": "1020304"})
    assert r.status_code == 409


def test_r03_busqueda_por_nombre_o_documento(cliente_admin, cliente_empleado):
    crear_residente(cliente_admin, nombre="Zq Laura Gómez", numero_documento="7777777")
    crear_residente(cliente_admin, nombre="Zq Mario Ruiz", numero_documento="8888888")

    def nombres(texto):
        r = cliente_empleado.get(URL, params={"texto": texto})
        assert r.status_code == 200
        return [x["nombre"] for x in r.json()]

    assert nombres("zq") == ["Zq Laura Gómez", "Zq Mario Ruiz"]
    assert nombres("laura") == ["Zq Laura Gómez"]
    assert nombres("8.888.888") == ["Zq Mario Ruiz"]


def test_r04_detalle_con_bloqueo_activo(cliente_admin, cliente_empleado):
    residente = crear_residente(cliente_admin)
    assert cliente_admin.get(f"{URL}/{residente['id']}").json()["bloqueo_activo"] is None

    crear_bloqueo(cliente_admin)
    detalle_admin = cliente_admin.get(f"{URL}/{residente['id']}").json()["bloqueo_activo"]
    assert detalle_admin["activo"] is True
    assert detalle_admin["motivo"] == "Dejó tres meses de arriendo sin pagar"

    # D-3: el empleado ve el bloqueo, pero no el motivo.
    detalle_empleado = cliente_empleado.get(f"{URL}/{residente['id']}").json()["bloqueo_activo"]
    assert detalle_empleado["activo"] is True
    assert detalle_empleado["motivo"] is None


def test_r04_el_bloqueo_sigue_al_documento_aunque_se_corrija(cliente_admin):
    crear_bloqueo(cliente_admin, numero_documento="4444444", nombre="Persona X")
    residente = crear_residente(cliente_admin, numero_documento="4444445")
    assert cliente_admin.get(f"{URL}/{residente['id']}").json()["bloqueo_activo"] is None
    cliente_admin.patch(f"{URL}/{residente['id']}", json={"numero_documento": "4444444"})
    assert cliente_admin.get(f"{URL}/{residente['id']}").json()["bloqueo_activo"] is not None


def test_r12_crear_y_editar_quedan_auditados(cliente_admin, sesion_bd):
    residente = crear_residente(cliente_admin)
    cliente_admin.patch(f"{URL}/{residente['id']}", json={"telefono": "300 000 0000"})
    crear, editar = auditorias(sesion_bd, residente["id"])
    assert crear.accion == "residente.crear"
    assert editar.valor_anterior == {"telefono": "310 555 1234"}
    assert editar.valor_nuevo == {"telefono": "300 000 0000"}


def test_residente_inexistente_responde_404(cliente_admin):
    assert cliente_admin.get(f"{URL}/999999").status_code == 404
    assert cliente_admin.patch(f"{URL}/999999", json={"nombre": "X"}).status_code == 404
