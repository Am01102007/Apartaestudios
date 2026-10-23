"""Datos de ejemplo para contratos. El reloj de pruebas empieza el 17 de octubre de 2026."""

from fastapi.testclient import TestClient

from tests.integration.ayudas import ingresar
from tests.integration.ayudas_inmuebles import crear_apartaestudio, crear_propietario
from tests.integration.ayudas_personas import crear_residente


def datos_contrato(apartaestudio_id: int, residente_id: int, **cambios) -> dict:
    return {
        "apartaestudio_id": apartaestudio_id,
        "residente_id": residente_id,
        "fecha_inicio": "2026-10-20",
        "fecha_terminacion": "2027-10-19",
        "canon_inicial": "850000",
        "porcentaje_incremento": "5.00",
    } | cambios


def crear_contrato(cliente: TestClient, apartaestudio_id: int, residente_id: int, **cambios):
    r = cliente.post(
        "/api/v1/contratos", json=datos_contrato(apartaestudio_id, residente_id, **cambios)
    )
    assert r.status_code == 201, r.text
    return r.json()


def escenario(cliente_admin: TestClient) -> tuple[dict, dict]:
    """Un apartaestudio activo y un residente sin bloqueo."""
    propietario = crear_propietario(cliente_admin)
    return crear_apartaestudio(cliente_admin, propietario["id"]), crear_residente(cliente_admin)


def pasar_dias(reloj, *clientes_y_usuarios: tuple[TestClient, str], dias: int) -> None:
    """Avanza el reloj y vuelve a iniciar sesión, porque la sesión expira por inactividad."""
    reloj.avanzar(days=dias)
    for cliente, usuario in clientes_y_usuarios:
        cliente.cookies.clear()
        assert ingresar(cliente, usuario).status_code == 200
