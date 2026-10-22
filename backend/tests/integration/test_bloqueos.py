"""Bloqueos (R-05 a R-12; RF-07, RN-07)."""

import pytest
from sqlalchemy import select, text

from app.core.errores import ReglaDeNegocio
from app.modulos.auditoria.modelos import RegistroAuditoria
from app.modulos.bloqueos import servicio
from tests.integration.ayudas_personas import (
    crear_bloqueo,
    datos_bloqueo,
)

pytestmark = pytest.mark.integracion
URL = "/api/v1/bloqueos"
MOTIVO = "Dejó tres meses de arriendo sin pagar"


def test_r05_bloquear_guarda_motivo_momento_y_responsable(cliente_admin):
    bloqueo = crear_bloqueo(cliente_admin, numero_documento="1.020.304")
    assert bloqueo["numero_documento"] == "1020304"
    assert bloqueo["activo"] is True
    assert bloqueo["motivo"] == MOTIVO
    assert bloqueo["bloqueado_en"].startswith("2026-10-17T15:00")
    assert bloqueo["bloqueado_por"]["nombre"] == "Admin"
    assert bloqueo["levantado_en"] is None


@pytest.mark.parametrize("cambios", [{"motivo": ""}, {"motivo": "ab"}, {"nombre": ""}])
def test_r05_motivo_y_nombre_son_obligatorios(cliente_admin, cambios):
    assert cliente_admin.post(URL, json=datos_bloqueo(**cambios)).status_code == 422


def test_r06_no_hay_dos_bloqueos_activos_para_el_mismo_documento(cliente_admin):
    crear_bloqueo(cliente_admin)
    r = cliente_admin.post(URL, json=datos_bloqueo(numero_documento="1 020 304"))
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "ya_bloqueado"
    # Otro tipo de documento con el mismo número es otra persona.
    assert cliente_admin.post(URL, json=datos_bloqueo(tipo_documento="CE")).status_code == 201


def test_r07_r08_levantar_conserva_el_historial_y_permite_volver_a_bloquear(cliente_admin, reloj):
    bloqueo = crear_bloqueo(cliente_admin)
    ruta = f"{URL}/{bloqueo['id']}/levantar"
    assert cliente_admin.post(ruta, json={}).status_code == 422  # sin motivo

    reloj.avanzar(minutes=20)
    r = cliente_admin.post(ruta, json={"motivo": "Pagó la deuda completa"})
    assert r.status_code == 200
    levantado = r.json()
    assert levantado["activo"] is False
    assert levantado["levantado_en"].startswith("2026-10-17T15:20")
    assert levantado["levantado_por"]["nombre"] == "Admin"
    assert levantado["motivo"] == MOTIVO  # el motivo original se conserva
    assert levantado["motivo_levantamiento"] == "Pagó la deuda completa"

    r = cliente_admin.post(ruta, json={"motivo": "Otra vez"})
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "ya_levantado"

    nuevo = crear_bloqueo(cliente_admin, motivo="Volvió a incumplir")
    historial = cliente_admin.get(URL, params={"estado": "todos", "texto": "1020304"}).json()
    assert [b["id"] for b in historial] == [nuevo["id"], bloqueo["id"]]
    assert [b["activo"] for b in historial] == [True, False]


def test_listar_por_estado(cliente_admin):
    activo = crear_bloqueo(cliente_admin, numero_documento="6000001", nombre="Zk Activo")
    levantado = crear_bloqueo(cliente_admin, numero_documento="6000002", nombre="Zk Levantado")
    cliente_admin.post(f"{URL}/{levantado['id']}/levantar", json={"motivo": "Error de digitación"})

    def ids(estado=None):
        params = {"texto": "zk"} | ({"estado": estado} if estado else {})
        return {b["id"] for b in cliente_admin.get(URL, params=params).json()}

    assert ids() == {activo["id"]}  # por defecto, solo activos
    assert ids("levantados") == {levantado["id"]}
    assert ids("todos") == {activo["id"], levantado["id"]}


def test_r09_verificar_un_documento(cliente_admin, cliente_empleado):
    params = {"tipo_documento": "CC", "numero_documento": "1.020.304"}
    assert cliente_empleado.get(f"{URL}/verificar", params=params).json() == {
        "bloqueado": False,
        "bloqueo_id": None,
        "desde": None,
    }
    bloqueo = crear_bloqueo(cliente_admin)
    r = cliente_empleado.get(f"{URL}/verificar", params=params)
    assert r.status_code == 200
    assert r.json()["bloqueado"] is True
    assert r.json()["bloqueo_id"] == bloqueo["id"]
    assert "motivo" not in r.json()

    assert (
        cliente_empleado.get(
            f"{URL}/verificar", params={"tipo_documento": "XX", "numero_documento": "1"}
        ).status_code
        == 422
    )


def test_r10_un_bloqueo_no_se_borra_ni_hay_endpoint_para_editarlo(cliente_admin, app):
    rutas = {(m.upper(), r) for r, ops in app.openapi()["paths"].items() for m in ops}
    assert not any(
        r.startswith("/api/v1/bloqueos") and m in ("DELETE", "PATCH", "PUT") for m, r in rutas
    )


def test_r10_la_base_exige_un_levantamiento_completo(cliente_admin, sesion_bd):
    bloqueo = crear_bloqueo(cliente_admin)
    with pytest.raises(Exception, match="levantamiento_completo"), sesion_bd.begin_nested():
        sesion_bd.execute(
            text("UPDATE bloqueos SET levantado_en = now() WHERE id = :id"), {"id": bloqueo["id"]}
        )


def test_r11_el_empleado_ve_los_bloqueos_sin_motivos(cliente_admin, cliente_empleado):
    bloqueo = crear_bloqueo(cliente_admin)
    cliente_admin.post(f"{URL}/{bloqueo['id']}/levantar", json={"motivo": "Pagó la deuda"})
    crear_bloqueo(cliente_admin, motivo="Volvió a incumplir")

    lista = cliente_empleado.get(URL, params={"estado": "todos", "texto": "1020304"}).json()
    assert len(lista) == 2
    assert all(b["motivo"] is None and b["motivo_levantamiento"] is None for b in lista)
    assert all(b["nombre"] == "Carlos Pérez" for b in lista)

    admin = cliente_admin.get(URL, params={"estado": "todos", "texto": "1020304"}).json()
    assert {b["motivo"] for b in admin} == {MOTIVO, "Volvió a incumplir"}


def test_r11_el_empleado_no_bloquea_ni_levanta(cliente_admin, cliente_empleado):
    bloqueo = crear_bloqueo(cliente_admin)
    assert (
        cliente_empleado.post(URL, json=datos_bloqueo(numero_documento="1111111")).status_code
        == 403
    )
    r = cliente_empleado.post(f"{URL}/{bloqueo['id']}/levantar", json={"motivo": "Pagó"})
    assert r.status_code == 403


def test_r12_bloquear_y_levantar_quedan_auditados(cliente_admin, sesion_bd):
    bloqueo = crear_bloqueo(cliente_admin)
    cliente_admin.post(f"{URL}/{bloqueo['id']}/levantar", json={"motivo": "Pagó la deuda"})
    registros = sesion_bd.scalars(
        select(RegistroAuditoria)
        .where(
            RegistroAuditoria.entidad == "bloqueo",
            RegistroAuditoria.entidad_id == str(bloqueo["id"]),
        )
        .order_by(RegistroAuditoria.id)
    ).all()
    assert [r.accion for r in registros] == ["bloqueo.crear", "bloqueo.levantar"]
    assert registros[0].valor_nuevo["motivo"] == MOTIVO
    assert registros[1].valor_nuevo == {"activo": False, "motivo": "Pagó la deuda"}
    assert all(r.usuario_id is not None for r in registros)


def test_exigir_sin_bloqueo_para_el_modulo_de_contratos(cliente_admin, sesion_bd):
    servicio.exigir_sin_bloqueo(sesion_bd, "CC", "1020304")  # sin bloqueo: no falla
    crear_bloqueo(cliente_admin)
    with pytest.raises(ReglaDeNegocio) as error:
        servicio.exigir_sin_bloqueo(sesion_bd, "CC", "1020304")
    assert error.value.codigo == "persona_bloqueada"


def test_bloqueo_inexistente_responde_404(cliente_admin):
    r = cliente_admin.post(f"{URL}/999999/levantar", json={"motivo": "Pagó la deuda"})
    assert r.status_code == 404
