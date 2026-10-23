"""Prorrogar, renovar, terminar e historial (C-09, C-11 a C-13, C-17).

El reloj de pruebas empieza el 17 de octubre de 2026 en Bogotá.
"""

from datetime import date, timedelta

import pytest
from sqlalchemy import select

from app.modulos.contratos import consultas, estados
from app.modulos.contratos.modelos import Contrato
from tests.integration.ayudas_contratos import crear_contrato, escenario, pasar_dias
from tests.integration.ayudas_personas import crear_bloqueo

pytestmark = pytest.mark.integracion
URL = "/api/v1/contratos"


@pytest.fixture
def vigente(cliente_admin):
    """Contrato vigente del 17 de octubre de 2026 al 16 de octubre de 2027."""
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(
        cliente_admin,
        apartaestudio["id"],
        residente["id"],
        fecha_inicio="2026-10-17",
        fecha_terminacion="2027-10-16",
    )
    assert contrato["estado"] == "vigente"
    return contrato


# --- Prórroga -------------------------------------------------------------------------------


def test_c11_prorroga_extiende_el_mismo_contrato(cliente_empleado, vigente):
    url = f"{URL}/{vigente['id']}/prorrogar"
    r = cliente_empleado.post(url, json={"fecha_terminacion": "2028-10-16"})
    assert r.status_code == 200, r.text
    assert r.json()["id"] == vigente["id"]
    assert r.json()["fecha_terminacion"] == "2028-10-16"
    [prorroga] = r.json()["prorrogas"]
    assert prorroga["terminacion_anterior"] == "2027-10-16"
    assert prorroga["terminacion_nueva"] == "2028-10-16"
    assert prorroga["registrada_por"]["nombre"] == "Empleado"
    # La nueva terminación debe ser posterior a la actual.
    assert cliente_empleado.post(url, json={"fecha_terminacion": "2028-10-16"}).status_code == 422


def test_c11_un_contrato_vencido_que_se_prorroga_vuelve_a_vigente(cliente_admin, reloj):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(
        cliente_admin,
        apartaestudio["id"],
        residente["id"],
        fecha_inicio="2026-10-17",
        fecha_terminacion="2026-11-16",
    )
    pasar_dias(reloj, (cliente_admin, "admin"), dias=40)  # 26 de noviembre
    url = f"{URL}/{contrato['id']}"
    assert cliente_admin.get(url).json()["estado"] == "vencido"
    r = cliente_admin.post(f"{url}/prorrogar", json={"fecha_terminacion": "2026-11-25"})
    assert r.status_code == 422  # anterior a hoy
    r = cliente_admin.post(f"{url}/prorrogar", json={"fecha_terminacion": "2027-11-16"})
    assert r.json()["estado"] == "vigente"
    # Los aniversarios siguen contando desde el inicio original (RN-29).
    assert r.json()["proximo_aniversario"] == "2027-10-17"


def test_rn07_la_prorroga_se_permite_aunque_la_persona_este_bloqueada(cliente_admin, vigente):
    crear_bloqueo(cliente_admin, numero_documento=vigente["residente"]["numero_documento"])
    r = cliente_admin.post(
        f"{URL}/{vigente['id']}/prorrogar", json={"fecha_terminacion": "2028-10-16"}
    )
    assert r.status_code == 200


def test_un_contrato_por_iniciar_no_se_prorroga(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])
    r = cliente_admin.post(
        f"{URL}/{contrato['id']}/prorrogar", json={"fecha_terminacion": "2028-10-16"}
    )
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "estado_no_permite"


# --- Renovación -----------------------------------------------------------------------------


def test_c12_d2_renovacion_enlazada_sin_hueco_ni_traslape(cliente_empleado, vigente, reloj):
    url = f"{URL}/{vigente['id']}"
    r = cliente_empleado.post(
        f"{url}/renovar",
        json={"fecha_terminacion": "2028-10-16", "porcentaje_incremento": "4.00"},
    )
    assert r.status_code == 201, r.text
    nuevo = r.json()
    assert nuevo["fecha_inicio"] == "2027-10-17"  # día siguiente a la terminación (D-2)
    assert nuevo["estado"] == "por_iniciar"
    assert nuevo["contrato_anterior_id"] == vigente["id"]
    assert nuevo["canon_inicial"] == vigente["canon_vigente"]
    assert nuevo["apartaestudio"]["id"] == vigente["apartaestudio"]["id"]

    anterior = cliente_empleado.get(url).json()
    assert anterior["estado"] == "vigente"
    assert anterior["contrato_siguiente_id"] == nuevo["id"]
    # D-4: el contrato nuevo cuenta sus aniversarios desde su propio inicio.
    assert cliente_empleado.get(f"{URL}/{nuevo['id']}").json()["proximo_aniversario"] == (
        "2028-10-17"
    )

    pasar_dias(reloj, (cliente_empleado, "empleado"), dias=365)  # 17 de octubre de 2027
    assert cliente_empleado.get(url).json()["estado"] == "renovado"
    assert cliente_empleado.get(f"{URL}/{nuevo['id']}").json()["estado"] == "vigente"
    ocupacion = cliente_empleado.get(
        f"/api/v1/apartaestudios/{vigente['apartaestudio']['id']}"
    ).json()["ocupacion"]
    assert ocupacion == "ocupado"


def test_d2_renovacion_de_un_contrato_vencido_empieza_en_el_siguiente_periodo(cliente_admin, reloj):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(
        cliente_admin,
        apartaestudio["id"],
        residente["id"],
        fecha_inicio="2026-10-17",
        fecha_terminacion="2026-11-16",
    )
    pasar_dias(reloj, (cliente_admin, "admin"), dias=40)  # 26 de noviembre: vencido
    r = cliente_admin.post(
        f"{URL}/{contrato['id']}/renovar",
        json={
            "fecha_terminacion": "2027-12-16",
            "canon_inicial": "900000",
            "porcentaje_incremento": "5",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["fecha_inicio"] == "2026-12-17"
    assert r.json()["canon_inicial"] == "900000"
    # Hasta el cambio, el anterior sigue vencido (y ocupando el apartaestudio).
    assert cliente_admin.get(f"{URL}/{contrato['id']}").json()["estado"] == "vencido"


def test_ca03_persona_bloqueada_no_renueva(cliente_admin, vigente):
    crear_bloqueo(cliente_admin, numero_documento=vigente["residente"]["numero_documento"])
    r = cliente_admin.post(
        f"{URL}/{vigente['id']}/renovar",
        json={"fecha_terminacion": "2028-10-16", "porcentaje_incremento": "4"},
    )
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "persona_bloqueada"


def test_un_contrato_se_renueva_una_sola_vez_y_ya_no_se_prorroga_ni_termina(cliente_admin, vigente):
    url = f"{URL}/{vigente['id']}"
    renovacion = {"fecha_terminacion": "2028-10-16", "porcentaje_incremento": "4"}
    assert cliente_admin.post(f"{url}/renovar", json=renovacion).status_code == 201
    for accion, cuerpo in [
        ("renovar", renovacion),
        ("prorrogar", {"fecha_terminacion": "2028-01-01"}),
        (
            "terminar",
            {"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-12-01", "motivo": "Se muda"},
        ),
    ]:
        r = cliente_admin.post(f"{url}/{accion}", json=cuerpo)
        assert r.status_code == 409, accion
        assert r.json()["error"]["codigo"] == "ya_renovado"
    assert cliente_admin.patch(url, json={"notas": "x"}).json()["error"]["codigo"] == "ya_renovado"


def test_la_terminacion_de_la_renovacion_debe_ser_posterior_a_su_inicio(cliente_admin, vigente):
    r = cliente_admin.post(
        f"{URL}/{vigente['id']}/renovar",
        json={"fecha_terminacion": "2027-10-17", "porcentaje_incremento": "4"},
    )
    assert r.status_code == 422
    assert "2027-10-17" in r.json()["error"]["mensaje"]


def test_anular_la_renovacion_permite_renovar_de_nuevo(cliente_admin, vigente):
    url = f"{URL}/{vigente['id']}"
    renovacion = {"fecha_terminacion": "2028-10-16", "porcentaje_incremento": "4"}
    nuevo = cliente_admin.post(f"{url}/renovar", json=renovacion).json()
    r = cliente_admin.post(f"{URL}/{nuevo['id']}/anular", json={"motivo": "Cambió de idea"})
    assert r.status_code == 200 and r.json()["estado"] == "anulado"
    anterior = cliente_admin.get(url).json()
    assert anterior["contrato_siguiente_id"] is None
    assert anterior["proximo_aniversario"] == "2027-10-17"
    assert cliente_admin.post(f"{url}/renovar", json=renovacion).status_code == 201


# --- Terminación ----------------------------------------------------------------------------


def test_c13_terminar_registra_aviso_entrega_y_motivo(cliente_empleado, vigente, reloj):
    url = f"{URL}/{vigente['id']}"
    r = cliente_empleado.post(
        f"{url}/terminar",
        json={"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-11-30", "motivo": "Se muda"},
    )
    assert r.status_code == 200, r.text
    contrato = r.json()
    assert contrato["estado"] == "en_terminacion"
    assert (contrato["fecha_aviso"], contrato["fecha_entrega"]) == ("2026-10-17", "2026-11-30")
    assert contrato["motivo_terminacion"] == "Se muda"
    assert contrato["proximo_corte"] == "2026-10-17"  # hoy es día de corte
    assert contrato["proximo_aniversario"] is None  # después de la entrega

    pasar_dias(reloj, (cliente_empleado, "empleado"), dias=45)  # 1 de diciembre
    assert cliente_empleado.get(url).json()["estado"] == "terminado"
    assert cliente_empleado.get(url).json()["proximo_corte"] is None


def test_d3_la_fecha_de_entrega_se_corrige_mientras_no_haya_pasado(cliente_admin, vigente, reloj):
    url = f"{URL}/{vigente['id']}/terminar"
    terminacion = {"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-11-30", "motivo": "Se muda"}
    cliente_admin.post(url, json=terminacion)
    r = cliente_admin.post(url, json=terminacion | {"fecha_entrega": "2026-12-15"})
    assert r.status_code == 200 and r.json()["fecha_entrega"] == "2026-12-15"

    pasar_dias(reloj, (cliente_admin, "admin"), dias=60)  # 16 de diciembre: ya terminado
    r = cliente_admin.post(url, json=terminacion | {"fecha_entrega": "2026-12-31"})
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "estado_no_permite"


def test_validaciones_de_la_terminacion(cliente_admin, vigente):
    url = f"{URL}/{vigente['id']}/terminar"
    base = {"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-11-30", "motivo": "Se muda"}
    assert cliente_admin.post(url, json=base | {"fecha_aviso": "2026-10-18"}).status_code == 422
    assert cliente_admin.post(url, json=base | {"fecha_entrega": "2026-10-16"}).status_code == 422
    assert cliente_admin.post(url, json=base | {"motivo": "x"}).status_code == 422


def test_un_contrato_por_iniciar_no_se_termina_se_anula(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])
    r = cliente_admin.post(
        f"{URL}/{contrato['id']}/terminar",
        json={"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-11-30", "motivo": "Se muda"},
    )
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "estado_no_permite"


# --- Historial y estado ---------------------------------------------------------------------


def test_c17_historial_con_autor_y_fecha(cliente_admin, cliente_empleado, vigente):
    url = f"{URL}/{vigente['id']}"
    cliente_empleado.post(f"{url}/prorrogar", json={"fecha_terminacion": "2028-10-16"})
    cliente_admin.post(
        f"{url}/terminar",
        json={"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-11-30", "motivo": "Se muda"},
    )
    cliente_admin.post(
        f"{url}/terminar",
        json={"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-12-15", "motivo": "Se muda"},
    )
    historial = cliente_empleado.get(f"{url}/historial").json()
    assert [(c["accion"], c["usuario"]["nombre"]) for c in historial] == [
        ("contrato.crear", "Admin"),
        ("contrato.prorrogar", "Empleado"),
        ("contrato.terminar", "Admin"),
        ("contrato.corregir_terminacion", "Admin"),
    ]
    assert historial[1]["valor_anterior"] == {"fecha_terminacion": "2027-10-16"}
    assert historial[3]["valor_anterior"]["fecha_entrega"] == "2026-11-30"
    assert cliente_empleado.get(f"{URL}/999999/historial").status_code == 404


def test_c09_el_estado_en_sql_coincide_con_las_reglas_en_python(cliente_admin, sesion_bd):
    """La lista filtra con SQL y el detalle calcula con Python: deben dar lo mismo cada día."""
    apartaestudio, residente = escenario(cliente_admin)
    crear_contrato(
        cliente_admin,
        apartaestudio["id"],
        residente["id"],
        fecha_inicio="2026-10-17",
        fecha_terminacion="2026-11-16",
    )
    contrato = sesion_bd.scalar(select(Contrato).where(Contrato.residente_id == residente["id"]))
    contrato.fecha_aviso, contrato.fecha_entrega = date(2026, 11, 20), date(2026, 11, 25)
    contrato.motivo_terminacion, contrato.fin_reserva = "Se muda", date(2026, 11, 25)
    contrato.terminacion_registrada_por_id = contrato.creado_por_id
    sesion_bd.flush()
    for desplazamiento in range(-2, 45):
        dia = date(2026, 10, 17) + timedelta(days=desplazamiento)
        en_sql = sesion_bd.scalar(select(consultas.estado(dia)).where(Contrato.id == contrato.id))
        en_python = estados.estado(
            dia,
            fecha_inicio=contrato.fecha_inicio,
            fecha_terminacion=contrato.fecha_terminacion,
            fecha_entrega=contrato.fecha_entrega,
            fin_reserva=contrato.fin_reserva,
            anulado=False,
        )
        assert en_sql == en_python, dia
