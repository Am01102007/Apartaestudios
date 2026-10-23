"""Crear, consultar, editar y anular contratos; ocupación real (C-01 a C-10, C-14, C-16).

El reloj de pruebas empieza el 17 de octubre de 2026 en Bogotá.
"""

import pytest

from tests.integration.ayudas_contratos import (
    crear_contrato,
    datos_contrato,
    escenario,
    pasar_dias,
)
from tests.integration.ayudas_inmuebles import crear_apartaestudio
from tests.integration.ayudas_personas import crear_bloqueo, crear_residente

pytestmark = pytest.mark.integracion
URL = "/api/v1/contratos"


def test_c01_ambos_roles_crean_contratos(cliente_admin, cliente_empleado):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(cliente_empleado, apartaestudio["id"], residente["id"])
    assert contrato["estado"] == "por_iniciar"
    assert contrato["canon_inicial"] == "850000"
    assert contrato["canon_vigente"] == "850000"
    assert contrato["porcentaje_incremento"] == "5.00"
    assert contrato["dia_corte"] == 20
    assert contrato["proximo_corte"] == "2026-10-20"
    assert contrato["proximo_aniversario"] == "2027-10-20"
    assert contrato["apartaestudio"]["codigo"] == apartaestudio["codigo"]
    assert contrato["residente"]["nombre"] == residente["nombre"]
    assert contrato["creado_por"]["nombre"] == "Empleado"


@pytest.mark.parametrize(
    ("cambios", "campo"),
    [
        ({"fecha_terminacion": "2026-10-20"}, ""),
        ({"canon_inicial": "0"}, "canon_inicial"),
        ({"canon_inicial": "850000.50"}, "canon_inicial"),
        ({"porcentaje_incremento": "100.01"}, "porcentaje_incremento"),
        ({"porcentaje_incremento": "4.555"}, "porcentaje_incremento"),
    ],
)
def test_c02_validaciones_de_fechas_y_montos(cliente_admin, cambios, campo):
    apartaestudio, residente = escenario(cliente_admin)
    r = cliente_admin.post(
        URL, json=datos_contrato(apartaestudio["id"], residente["id"], **cambios)
    )
    assert r.status_code == 422, r.text
    assert any(d["campo"] == campo for d in r.json()["error"]["detalles"]), r.json()


def test_d1_no_se_registran_contratos_con_inicio_pasado(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    r = cliente_admin.post(
        URL, json=datos_contrato(apartaestudio["id"], residente["id"], fecha_inicio="2026-10-16")
    )
    assert r.status_code == 422
    assert r.json()["error"]["detalles"][0]["campo"] == "fecha_inicio"
    crear_contrato(cliente_admin, apartaestudio["id"], residente["id"], fecha_inicio="2026-10-17")


def test_ca01_apartaestudio_con_otro_contrato_se_rechaza_sin_guardar(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])
    otro = crear_residente(cliente_admin, numero_documento="55667788", nombre="Otra")
    # Aunque empiece mucho después del primero: RN-04 rechaza mientras exista.
    r = cliente_admin.post(
        URL,
        json=datos_contrato(
            apartaestudio["id"],
            otro["id"],
            fecha_inicio="2028-01-01",
            fecha_terminacion="2029-01-01",
        ),
    )
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "apartaestudio_reservado"
    assert len(cliente_admin.get(URL, params={"apartaestudio_id": apartaestudio["id"]}).json()) == 1


def test_ca02_inicio_el_dia_de_la_entrega_se_rechaza_y_al_dia_siguiente_se_acepta(
    cliente_admin, reloj
):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(
        cliente_admin, apartaestudio["id"], residente["id"], fecha_inicio="2026-10-17"
    )
    r = cliente_admin.post(
        f"{URL}/{contrato['id']}/terminar",
        json={"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-10-25", "motivo": "Se muda"},
    )
    assert r.status_code == 200, r.text
    otro = crear_residente(cliente_admin, numero_documento="55667788", nombre="Otra")
    nuevo = datos_contrato(apartaestudio["id"], otro["id"], fecha_inicio="2026-10-25")

    pasar_dias(reloj, (cliente_admin, "admin"), dias=8)  # 25 de octubre, día de la entrega
    r = cliente_admin.post(URL, json=nuevo)
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "apartaestudio_reservado"

    pasar_dias(reloj, (cliente_admin, "admin"), dias=1)  # 26 de octubre
    r = cliente_admin.post(URL, json=nuevo | {"fecha_inicio": "2026-10-26"})
    assert r.status_code == 201, r.text


def test_ca02_la_base_de_datos_rechaza_el_cruce_aunque_el_servicio_lo_permita(
    cliente_admin, reloj, monkeypatch
):
    from app.modulos.contratos import repositorio

    monkeypatch.setattr(repositorio, "apartaestudio_reservado", lambda *a, **k: False)
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(
        cliente_admin, apartaestudio["id"], residente["id"], fecha_inicio="2026-10-17"
    )
    cliente_admin.post(
        f"{URL}/{contrato['id']}/terminar",
        json={"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-10-25", "motivo": "Se muda"},
    )
    otro = crear_residente(cliente_admin, numero_documento="55667788", nombre="Otra")
    mismo_dia = datos_contrato(apartaestudio["id"], otro["id"], fecha_inicio="2026-10-25")
    r = cliente_admin.post(URL, json=mismo_dia)
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "apartaestudio_reservado"
    r = cliente_admin.post(URL, json=mismo_dia | {"fecha_inicio": "2026-10-26"})
    assert r.status_code == 201, r.text


def test_ca03_persona_bloqueada_no_firma(cliente_admin, cliente_empleado):
    apartaestudio, residente = escenario(cliente_admin)
    crear_bloqueo(cliente_admin, numero_documento=residente["numero_documento"])
    r = cliente_empleado.post(URL, json=datos_contrato(apartaestudio["id"], residente["id"]))
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "persona_bloqueada"
    assert cliente_admin.get(URL).json() == []


def test_c07_una_persona_puede_tener_varios_contratos(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    otro = crear_apartaestudio(cliente_admin, apartaestudio["propietario"]["id"], codigo="202")
    crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])
    crear_contrato(cliente_admin, otro["id"], residente["id"])
    assert len(cliente_admin.get(f"/api/v1/residentes/{residente['id']}/contratos").json()) == 2


def test_c08_apartaestudio_inactivo_no_y_en_mantenimiento_si(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    cliente_admin.post(
        f"/api/v1/apartaestudios/{apartaestudio['id']}/mantenimiento",
        json={"activo": True, "motivo": "Pintura"},
    )
    crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])

    otro = crear_apartaestudio(cliente_admin, apartaestudio["propietario"]["id"], codigo="202")
    cliente_admin.post(f"/api/v1/apartaestudios/{otro['id']}/desactivar")
    r = cliente_admin.post(URL, json=datos_contrato(otro["id"], residente["id"]))
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "apartaestudio_inactivo"


def test_partes_inexistentes_responden_404(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    assert cliente_admin.post(URL, json=datos_contrato(999999, residente["id"])).status_code == 404
    assert (
        cliente_admin.post(URL, json=datos_contrato(apartaestudio["id"], 999999)).status_code == 404
    )


def _ocupacion(cliente, apartaestudio_id):
    detalle = cliente.get(f"/api/v1/apartaestudios/{apartaestudio_id}").json()["ocupacion"]
    lista = {a["id"]: a["ocupacion"] for a in cliente.get("/api/v1/apartaestudios").json()}[
        apartaestudio_id
    ]
    ocupados = {a["id"] for a in cliente.get("/api/v1/apartaestudios?ocupacion=ocupado").json()}
    assert detalle == lista
    assert (apartaestudio_id in ocupados) == (detalle == "ocupado")
    return detalle


def test_ca04_ocupado_si_y_solo_si_hay_contrato_vigente_vencido_o_en_terminacion(
    cliente_admin, reloj
):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(
        cliente_admin,
        apartaestudio["id"],
        residente["id"],
        fecha_inicio="2026-10-18",
        fecha_terminacion="2026-11-17",
    )
    url = f"{URL}/{contrato['id']}"
    admin = (cliente_admin, "admin")

    assert _ocupacion(cliente_admin, apartaestudio["id"]) == "libre"  # por iniciar
    pasar_dias(reloj, admin, dias=1)  # 18 de octubre
    assert cliente_admin.get(url).json()["estado"] == "vigente"
    assert _ocupacion(cliente_admin, apartaestudio["id"]) == "ocupado"
    pasar_dias(reloj, admin, dias=31)  # 18 de noviembre
    assert cliente_admin.get(url).json()["estado"] == "vencido"
    assert _ocupacion(cliente_admin, apartaestudio["id"]) == "ocupado"
    r = cliente_admin.post(
        f"{url}/terminar",
        json={"fecha_aviso": "2026-11-18", "fecha_entrega": "2026-11-20", "motivo": "Se muda"},
    )
    assert r.json()["estado"] == "en_terminacion"
    pasar_dias(reloj, admin, dias=2)  # 20 de noviembre, día de la entrega
    assert _ocupacion(cliente_admin, apartaestudio["id"]) == "ocupado"
    pasar_dias(reloj, admin, dias=1)
    assert cliente_admin.get(url).json()["estado"] == "terminado"
    assert _ocupacion(cliente_admin, apartaestudio["id"]) == "libre"


def test_c09_filtro_por_estado_y_propietario(cliente_admin, reloj):
    apartaestudio, residente = escenario(cliente_admin)
    otro = crear_apartaestudio(cliente_admin, apartaestudio["propietario"]["id"], codigo="202")
    crear_contrato(cliente_admin, apartaestudio["id"], residente["id"], fecha_inicio="2026-10-17")
    crear_contrato(cliente_admin, otro["id"], residente["id"])
    assert [c["estado"] for c in cliente_admin.get(URL, params={"estado": "vigente"}).json()] == [
        "vigente"
    ]
    assert len(cliente_admin.get(URL, params={"estado": "por_iniciar"}).json()) == 1
    propietario = apartaestudio["propietario"]["id"]
    assert len(cliente_admin.get(URL, params={"propietario_id": propietario}).json()) == 2
    assert cliente_admin.get(URL, params={"propietario_id": 999999}).json() == []


def test_editar_por_iniciar_y_validaciones(cliente_admin, cliente_empleado):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])
    url = f"{URL}/{contrato['id']}"
    r = cliente_empleado.patch(url, json={"canon_inicial": "900000", "fecha_inicio": "2026-10-22"})
    assert r.status_code == 200, r.text
    assert r.json()["canon_inicial"] == "900000" and r.json()["dia_corte"] == 22
    assert cliente_admin.patch(url, json={"fecha_inicio": "2026-10-16"}).status_code == 422
    assert cliente_admin.patch(url, json={"fecha_terminacion": "2026-10-22"}).status_code == 422
    assert cliente_admin.patch(url, json={"canon_inicial": None}).status_code == 422
    assert cliente_admin.patch(url, json={"residente_id": 1}).status_code == 422


def test_editar_contrato_vigente_no_cambia_el_inicio(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(
        cliente_admin, apartaestudio["id"], residente["id"], fecha_inicio="2026-10-17"
    )
    url = f"{URL}/{contrato['id']}"
    assert cliente_admin.patch(url, json={"fecha_inicio": "2026-10-20"}).status_code == 422
    assert cliente_admin.patch(url, json={"notas": "Incluye parqueadero"}).status_code == 200


def test_c15_contrato_con_cobros_no_se_edita(cliente_admin, monkeypatch):
    from app.modulos.contratos import servicio

    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])
    monkeypatch.setattr(servicio, "tiene_cobros", lambda *a: True)
    r = cliente_admin.patch(f"{URL}/{contrato['id']}", json={"canon_inicial": "900000"})
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "tiene_cobros"


def test_c14_solo_el_administrador_anula_contratos_por_iniciar(cliente_admin, cliente_empleado):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])
    url = f"{URL}/{contrato['id']}/anular"
    assert cliente_empleado.post(url, json={"motivo": "Error"}).status_code == 403
    assert cliente_admin.post(url, json={"motivo": "x"}).status_code == 422
    r = cliente_admin.post(url, json={"motivo": "El residente desistió"})
    assert r.status_code == 200 and r.json()["estado"] == "anulado"
    assert r.json()["motivo_anulacion"] == "El residente desistió"
    assert cliente_admin.post(url, json={"motivo": "Otra vez"}).status_code == 409
    # Anulado no reserva: el apartaestudio acepta otro contrato.
    crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])


def test_c14_un_contrato_vigente_no_se_anula(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(
        cliente_admin, apartaestudio["id"], residente["id"], fecha_inicio="2026-10-17"
    )
    r = cliente_admin.post(f"{URL}/{contrato['id']}/anular", json={"motivo": "Error"})
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "estado_no_permite"


def test_c16_no_se_desactiva_un_apartaestudio_con_contrato(cliente_admin, reloj):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(
        cliente_admin, apartaestudio["id"], residente["id"], fecha_inicio="2026-10-17"
    )
    url = f"/api/v1/apartaestudios/{apartaestudio['id']}/desactivar"
    r = cliente_admin.post(url)
    assert r.status_code == 409 and r.json()["error"]["codigo"] == "tiene_contrato"
    cliente_admin.post(
        f"{URL}/{contrato['id']}/terminar",
        json={"fecha_aviso": "2026-10-17", "fecha_entrega": "2026-10-18", "motivo": "Se muda"},
    )
    assert cliente_admin.post(url).status_code == 409  # en terminación
    pasar_dias(reloj, (cliente_admin, "admin"), dias=2)
    assert cliente_admin.post(url).status_code == 200


def test_detalle_del_residente_incluye_sus_contratos_actuales(cliente_admin, cliente_empleado):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])
    detalle = cliente_empleado.get(f"/api/v1/residentes/{residente['id']}").json()
    assert [c["id"] for c in detalle["contratos_actuales"]] == [contrato["id"]]
    cliente_admin.post(f"{URL}/{contrato['id']}/anular", json={"motivo": "Desistió"})
    assert (
        cliente_admin.get(f"/api/v1/residentes/{residente['id']}").json()["contratos_actuales"]
        == []
    )


def test_contratos_de_apartaestudio_y_residente_inexistentes(cliente_admin):
    assert cliente_admin.get("/api/v1/apartaestudios/999999/contratos").status_code == 404
    assert cliente_admin.get("/api/v1/residentes/999999/contratos").status_code == 404
    assert cliente_admin.get(f"{URL}/999999").status_code == 404


def test_c18_auditoria_de_crear_editar_y_anular(cliente_admin):
    apartaestudio, residente = escenario(cliente_admin)
    contrato = crear_contrato(cliente_admin, apartaestudio["id"], residente["id"])
    url = f"{URL}/{contrato['id']}"
    cliente_admin.patch(url, json={"canon_inicial": "900000"})
    cliente_admin.post(f"{url}/anular", json={"motivo": "Desistió"})
    auditoria = cliente_admin.get(
        "/api/v1/auditoria", params={"entidad": "contrato", "entidad_id": contrato["id"]}
    ).json()["registros"]
    acciones = [r["accion"] for r in auditoria]
    assert acciones == ["contrato.anular", "contrato.editar", "contrato.crear"]
    editar = auditoria[1]
    assert editar["valor_anterior"] == {"canon_inicial": "850000"}
    assert editar["valor_nuevo"] == {"canon_inicial": "900000"}
