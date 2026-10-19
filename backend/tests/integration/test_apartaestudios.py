"""Apartaestudios (P-04 a P-09, P-11, P-12; RF-04, RF-05, RN-02, RN-03)."""

import pytest
from sqlalchemy import select, text

from app.modulos.auditoria.modelos import RegistroAuditoria
from app.modulos.usuarios.modelos import Rol
from tests.integration.ayudas import crear_usuario, ingresar
from tests.integration.ayudas_inmuebles import (
    crear_apartaestudio,
    crear_propietario,
    datos_apartaestudio,
)

pytestmark = pytest.mark.integracion
URL = "/api/v1/apartaestudios"


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


@pytest.fixture
def propietario(cliente_admin):
    return crear_propietario(cliente_admin)


def auditorias(sesion_bd, entidad_id):
    return list(
        sesion_bd.scalars(
            select(RegistroAuditoria)
            .where(
                RegistroAuditoria.entidad == "apartaestudio",
                RegistroAuditoria.entidad_id == str(entidad_id),
            )
            .order_by(RegistroAuditoria.id)
        )
    )


def test_p04_crear_con_propietario_activo(cliente_admin, propietario):
    apto = crear_apartaestudio(cliente_admin, propietario["id"], codigo=" a-302 ")
    assert apto["codigo"] == "A-302"
    assert apto["propietario"] == {"id": propietario["id"], "nombre": "Ana Ruiz", "activo": True}
    assert apto["area_m2"] == "28.50"
    assert apto["ocupacion"] == "libre"
    assert apto["en_mantenimiento"] is False
    assert apto["activo"] is True


def test_p04_propietario_inexistente_o_inactivo_se_rechaza(cliente_admin, propietario):
    r = cliente_admin.post(URL, json=datos_apartaestudio(999999))
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "propietario_no_valido"

    cliente_admin.post(f"/api/v1/propietarios/{propietario['id']}/desactivar")
    r = cliente_admin.post(URL, json=datos_apartaestudio(propietario["id"]))
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "propietario_no_valido"


@pytest.mark.parametrize("variante", ["a-302", " A-302 ", "A-302"])
def test_p05_codigo_duplicado_sin_importar_mayusculas_ni_espacios(
    cliente_admin, propietario, variante
):
    crear_apartaestudio(cliente_admin, propietario["id"], codigo="A-302")
    r = cliente_admin.post(URL, json=datos_apartaestudio(propietario["id"], codigo=variante))
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "codigo_duplicado"


def test_p05_editar_hacia_un_codigo_existente_se_rechaza(cliente_admin, propietario):
    crear_apartaestudio(cliente_admin, propietario["id"], codigo="101")
    otro = crear_apartaestudio(cliente_admin, propietario["id"], codigo="102")
    r = cliente_admin.patch(f"{URL}/{otro['id']}", json={"codigo": "101"})
    assert r.status_code == 409


@pytest.mark.parametrize(
    "campo", [{"ocupacion": "ocupado"}, {"ocupado": True}, {"estado": "ocupado"}]
)
def test_p06_la_ocupacion_no_se_puede_enviar(cliente_admin, propietario, campo):
    r = cliente_admin.post(URL, json=datos_apartaestudio(propietario["id"]) | campo)
    assert r.status_code == 422
    apto = crear_apartaestudio(cliente_admin, propietario["id"])
    assert cliente_admin.patch(f"{URL}/{apto['id']}", json=campo).status_code == 422


def test_p07_marca_de_mantenimiento_con_motivo_y_responsable(
    cliente_admin, propietario, sesion_bd, reloj
):
    apto = crear_apartaestudio(cliente_admin, propietario["id"])
    ruta = f"{URL}/{apto['id']}/mantenimiento"

    assert cliente_admin.post(ruta, json={"activo": True}).status_code == 422  # sin motivo
    r = cliente_admin.post(ruta, json={"activo": True, "motivo": "Pintura de paredes"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["en_mantenimiento"] is True
    assert cuerpo["mantenimiento_motivo"] == "Pintura de paredes"
    assert cuerpo["mantenimiento_desde"].startswith("2026-10-17T15:00")
    assert cuerpo["mantenimiento_por_id"] is not None

    r = cliente_admin.post(ruta, json={"activo": True, "motivo": "Otra vez"})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "ya_en_mantenimiento"

    r = cliente_admin.post(ruta, json={"activo": False, "motivo": "Pintura terminada"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["en_mantenimiento"] is False
    assert cuerpo["mantenimiento_desde"] is None and cuerpo["mantenimiento_motivo"] is None

    r = cliente_admin.post(ruta, json={"activo": False, "motivo": "Otra vez"})
    assert r.json()["error"]["codigo"] == "sin_mantenimiento"

    acciones = [
        (a.accion, (a.valor_nuevo or {}).get("motivo")) for a in auditorias(sesion_bd, apto["id"])
    ]
    assert acciones == [
        ("apartaestudio.crear", None),
        ("apartaestudio.mantenimiento_activar", "Pintura de paredes"),
        ("apartaestudio.mantenimiento_retirar", "Pintura terminada"),
    ]


def test_p07_la_base_de_datos_no_admite_una_marca_a_medias(cliente_admin, propietario, sesion_bd):
    apto = crear_apartaestudio(cliente_admin, propietario["id"])
    with pytest.raises(Exception, match="mantenimiento_completo"), sesion_bd.begin_nested():
        sesion_bd.execute(
            text("UPDATE apartaestudios SET en_mantenimiento = true WHERE id = :id"),
            {"id": apto["id"]},
        )


def test_p08_mantenimiento_no_cambia_la_ocupacion(cliente_admin, propietario):
    apto = crear_apartaestudio(cliente_admin, propietario["id"])
    r = cliente_admin.post(
        f"{URL}/{apto['id']}/mantenimiento", json={"activo": True, "motivo": "Plomería"}
    )
    assert r.json()["ocupacion"] == "libre"
    assert cliente_admin.get(f"{URL}/{apto['id']}").json()["ocupacion"] == "libre"


def test_el_empleado_consulta_pero_no_modifica(cliente_admin, cliente_empleado, propietario):
    apto = crear_apartaestudio(cliente_admin, propietario["id"])
    assert cliente_empleado.get(f"{URL}/{apto['id']}").status_code == 200
    assert cliente_empleado.get(URL).status_code == 200
    r = cliente_empleado.post(
        f"{URL}/{apto['id']}/mantenimiento", json={"activo": True, "motivo": "Plomería"}
    )
    assert r.status_code == 403
    assert cliente_empleado.patch(f"{URL}/{apto['id']}", json={"direccion": "X"}).status_code == 403


def test_p09_filtros_de_la_lista(cliente_admin, propietario):
    otro = crear_propietario(cliente_admin, nombre="Luis Díaz", numero_documento="7654321")
    a = crear_apartaestudio(
        cliente_admin, propietario["id"], codigo="P9-101", direccion="Cra 7 # 1-1"
    )
    b = crear_apartaestudio(cliente_admin, propietario["id"], codigo="P9-102")
    c = crear_apartaestudio(cliente_admin, otro["id"], codigo="P9-201")
    cliente_admin.post(f"{URL}/{b['id']}/mantenimiento", json={"activo": True, "motivo": "Pintura"})
    cliente_admin.post(f"{URL}/{c['id']}/desactivar")

    def codigos(**params):
        r = cliente_admin.get(URL, params={"texto": "P9-"} | params)
        assert r.status_code == 200, r.text
        return [x["codigo"] for x in r.json()]

    assert codigos() == ["P9-101", "P9-102", "P9-201"]
    assert codigos(propietario_id=propietario["id"]) == ["P9-101", "P9-102"]
    assert codigos(en_mantenimiento=True) == ["P9-102"]
    assert codigos(activo=False) == ["P9-201"]
    assert codigos(ocupacion="libre") == ["P9-101", "P9-102", "P9-201"]
    assert codigos(ocupacion="ocupado") == []
    assert [x["codigo"] for x in cliente_admin.get(URL, params={"texto": "cra 7"}).json()] == [
        a["codigo"]
    ]
    assert cliente_admin.get(URL, params={"ocupacion": "en_obra"}).status_code == 422


def test_p11_cambio_de_propietario_queda_auditado(cliente_admin, propietario, sesion_bd):
    nuevo = crear_propietario(cliente_admin, nombre="Luis Díaz", numero_documento="7654321")
    apto = crear_apartaestudio(cliente_admin, propietario["id"])

    r = cliente_admin.patch(f"{URL}/{apto['id']}", json={"propietario_id": nuevo["id"]})
    assert r.status_code == 200
    assert r.json()["propietario"]["nombre"] == "Luis Díaz"

    edicion = auditorias(sesion_bd, apto["id"])[-1]
    assert edicion.accion == "apartaestudio.editar"
    assert edicion.valor_anterior == {"propietario_id": propietario["id"]}
    assert edicion.valor_nuevo == {"propietario_id": nuevo["id"]}


def test_p11_no_se_pasa_a_un_propietario_inactivo_ni_inexistente(cliente_admin, propietario):
    inactivo = crear_propietario(cliente_admin, nombre="Luis Díaz", numero_documento="7654321")
    cliente_admin.post(f"/api/v1/propietarios/{inactivo['id']}/desactivar")
    apto = crear_apartaestudio(cliente_admin, propietario["id"])
    for destino in (inactivo["id"], 999999):
        r = cliente_admin.patch(f"{URL}/{apto['id']}", json={"propietario_id": destino})
        assert r.status_code == 409
        assert r.json()["error"]["codigo"] == "propietario_no_valido"


def test_editar_cambia_solo_lo_enviado(cliente_admin, propietario, sesion_bd):
    apto = crear_apartaestudio(cliente_admin, propietario["id"], descripcion="Con balcón")
    r = cliente_admin.patch(f"{URL}/{apto['id']}", json={"area_m2": "30", "descripcion": None})
    assert r.status_code == 200
    assert r.json()["area_m2"] == "30.00"
    assert r.json()["descripcion"] is None
    assert r.json()["codigo"] == "201"
    edicion = auditorias(sesion_bd, apto["id"])[-1]
    assert edicion.valor_anterior == {"area_m2": "28.50", "descripcion": "Con balcón"}
    # Sin cambios reales no se audita nada.
    cliente_admin.patch(f"{URL}/{apto['id']}", json={"codigo": "201"})
    assert len(auditorias(sesion_bd, apto["id"])) == 2


def test_activar_exige_un_propietario_activo(cliente_admin, propietario):
    apto = crear_apartaestudio(cliente_admin, propietario["id"])
    cliente_admin.post(f"{URL}/{apto['id']}/desactivar")
    cliente_admin.post(f"/api/v1/propietarios/{propietario['id']}/desactivar")

    r = cliente_admin.post(f"{URL}/{apto['id']}/activar")
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "propietario_inactivo"

    cliente_admin.post(f"/api/v1/propietarios/{propietario['id']}/activar")
    r = cliente_admin.post(f"{URL}/{apto['id']}/activar")
    assert r.status_code == 200
    assert r.json()["activo"] is True


def test_apartaestudio_inexistente_responde_404(cliente_admin):
    assert cliente_admin.get(f"{URL}/999999").status_code == 404
    r = cliente_admin.post(f"{URL}/999999/mantenimiento", json={"activo": True, "motivo": "Xyz"})
    assert r.status_code == 404
