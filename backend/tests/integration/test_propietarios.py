"""Propietarios (P-01 a P-03, P-10, P-12; RF-03)."""

import pytest
from sqlalchemy import select

from app.modulos.auditoria.modelos import RegistroAuditoria
from app.modulos.usuarios.modelos import Rol
from tests.integration.ayudas import crear_usuario, ingresar
from tests.integration.ayudas_inmuebles import (
    crear_apartaestudio,
    crear_propietario,
    datos_propietario,
)

pytestmark = pytest.mark.integracion
URL = "/api/v1/propietarios"


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


def auditorias(sesion_bd, entidad_id):
    return list(
        sesion_bd.scalars(
            select(RegistroAuditoria)
            .where(
                RegistroAuditoria.entidad == "propietario",
                RegistroAuditoria.entidad_id == str(entidad_id),
            )
            .order_by(RegistroAuditoria.id)
        )
    )


def test_p01_el_administrador_crea_y_el_empleado_solo_consulta(cliente_admin, cliente_empleado):
    creado = crear_propietario(cliente_admin)
    assert creado["numero_documento"] == "1234567"
    assert creado["correo"] == "ana@correo.com"
    assert creado["activo"] is True

    r = cliente_empleado.post(URL, json=datos_propietario(numero_documento="999999"))
    assert r.status_code == 403
    r = cliente_empleado.get(f"{URL}/{creado['id']}")
    assert r.status_code == 200
    assert r.json()["nombre"] == "Ana Ruiz"


@pytest.mark.parametrize("variante", ["1234567", "1 234 567", "1-234-567"])
def test_p02_documento_duplicado_aunque_cambie_el_formato(cliente_admin, variante):
    crear_propietario(cliente_admin)
    r = cliente_admin.post(URL, json=datos_propietario(numero_documento=variante))
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "documento_duplicado"


def test_p02_mismo_numero_con_otro_tipo_de_documento_si_se_permite(cliente_admin):
    crear_propietario(cliente_admin)
    r = cliente_admin.post(URL, json=datos_propietario(tipo_documento="CE"))
    assert r.status_code == 201


def test_p02_editar_hacia_un_documento_existente_se_rechaza(cliente_admin):
    crear_propietario(cliente_admin)
    otro = crear_propietario(cliente_admin, numero_documento="7654321")
    r = cliente_admin.patch(f"{URL}/{otro['id']}", json={"numero_documento": "1.234.567"})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "documento_duplicado"


def test_editar_a_cedula_con_letras_se_rechaza(cliente_admin):
    pasaporte = crear_propietario(cliente_admin, tipo_documento="PA", numero_documento="AB12345")
    r = cliente_admin.patch(f"{URL}/{pasaporte['id']}", json={"tipo_documento": "CC"})
    assert r.status_code == 422


def test_p03_detalle_con_sus_apartaestudios_y_ocupacion(cliente_admin):
    propietario = crear_propietario(cliente_admin)
    otro = crear_propietario(cliente_admin, numero_documento="7654321")
    crear_apartaestudio(cliente_admin, propietario["id"], codigo="101")
    crear_apartaestudio(cliente_admin, propietario["id"], codigo="102")
    crear_apartaestudio(cliente_admin, otro["id"], codigo="201")

    r = cliente_admin.get(f"{URL}/{propietario['id']}")
    assert r.status_code == 200
    aptos = r.json()["apartaestudios"]
    assert [a["codigo"] for a in aptos] == ["101", "102"]
    assert {a["ocupacion"] for a in aptos} == {"libre"}


def test_editar_cambia_solo_lo_enviado_y_audita(cliente_admin, sesion_bd):
    propietario = crear_propietario(cliente_admin)
    r = cliente_admin.patch(
        f"{URL}/{propietario['id']}", json={"telefono": None, "nombre": "Ana María Ruiz"}
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["telefono"] is None
    assert cuerpo["nombre"] == "Ana María Ruiz"
    assert cuerpo["correo"] == "ana@correo.com"

    edicion = auditorias(sesion_bd, propietario["id"])[-1]
    assert edicion.accion == "propietario.editar"
    assert edicion.valor_anterior == {"nombre": "Ana Ruiz", "telefono": "+57 300 123 4567"}
    assert edicion.valor_nuevo == {"nombre": "Ana María Ruiz", "telefono": None}


def test_editar_no_admite_nulos_en_campos_obligatorios(cliente_admin):
    propietario = crear_propietario(cliente_admin)
    r = cliente_admin.patch(f"{URL}/{propietario['id']}", json={"nombre": None})
    assert r.status_code == 422


def test_p10_no_se_desactiva_con_apartaestudios_activos(cliente_admin):
    propietario = crear_propietario(cliente_admin)
    apto = crear_apartaestudio(cliente_admin, propietario["id"])

    r = cliente_admin.post(f"{URL}/{propietario['id']}/desactivar")
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "propietario_con_apartaestudios"

    assert cliente_admin.post(f"/api/v1/apartaestudios/{apto['id']}/desactivar").status_code == 200
    r = cliente_admin.post(f"{URL}/{propietario['id']}/desactivar")
    assert r.status_code == 200
    assert r.json()["activo"] is False


def test_desactivar_y_activar_conserva_los_datos(cliente_admin, sesion_bd):
    propietario = crear_propietario(cliente_admin)
    cliente_admin.post(f"{URL}/{propietario['id']}/desactivar")
    # Repetir no falla ni audita dos veces.
    cliente_admin.post(f"{URL}/{propietario['id']}/desactivar")
    r = cliente_admin.post(f"{URL}/{propietario['id']}/activar")
    assert r.json()["activo"] is True
    assert r.json()["numero_documento"] == "1234567"

    acciones = [a.accion for a in auditorias(sesion_bd, propietario["id"])]
    assert acciones == ["propietario.crear", "propietario.desactivar", "propietario.activar"]


def test_listar_filtra_por_texto_y_estado(cliente_admin):
    crear_propietario(
        cliente_admin,
        nombre="Zz Inversiones SAS",
        tipo_documento="NIT",
        numero_documento="900.123.456-7",
    )
    inactivo = crear_propietario(cliente_admin, nombre="Zz Pedro Pérez", numero_documento="555555")
    cliente_admin.post(f"{URL}/{inactivo['id']}/desactivar")

    nombres = [p["nombre"] for p in cliente_admin.get(URL, params={"texto": "zz"}).json()]
    assert nombres == ["Zz Inversiones SAS", "Zz Pedro Pérez"]
    activos = cliente_admin.get(URL, params={"texto": "zz", "activo": True}).json()
    assert [p["nombre"] for p in activos] == ["Zz Inversiones SAS"]
    por_documento = cliente_admin.get(URL, params={"texto": "9001234567"}).json()
    assert [p["nombre"] for p in por_documento] == ["Zz Inversiones SAS"]
    # Un % no actúa como comodín.
    assert cliente_admin.get(URL, params={"texto": "%"}).json() == []


def test_propietario_inexistente_responde_404(cliente_admin):
    assert cliente_admin.get(f"{URL}/999999").status_code == 404
    assert cliente_admin.patch(f"{URL}/999999", json={"nombre": "X"}).status_code == 404


def test_p12_crear_queda_auditado_con_el_autor(cliente_admin, sesion_bd):
    propietario = crear_propietario(cliente_admin)
    (registro,) = auditorias(sesion_bd, propietario["id"])
    assert registro.accion == "propietario.crear"
    assert registro.usuario_id is not None
    assert registro.valor_nuevo["numero_documento"] == "1234567"
