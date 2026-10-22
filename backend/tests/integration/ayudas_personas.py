"""Datos de ejemplo para residentes y bloqueos."""

from fastapi.testclient import TestClient


def datos_residente(**cambios) -> dict:
    return {
        "nombre": "Carlos Pérez",
        "tipo_documento": "CC",
        "numero_documento": "1.020.304",
        "telefono": "310 555 1234",
        "correo": "Carlos@Correo.com",
    } | cambios


def crear_residente(cliente: TestClient, **cambios) -> dict:
    r = cliente.post("/api/v1/residentes", json=datos_residente(**cambios))
    assert r.status_code == 201, r.text
    return r.json()


def datos_bloqueo(**cambios) -> dict:
    return {
        "tipo_documento": "CC",
        "numero_documento": "1020304",
        "nombre": "Carlos Pérez",
        "motivo": "Dejó tres meses de arriendo sin pagar",
    } | cambios


def crear_bloqueo(cliente: TestClient, **cambios) -> dict:
    r = cliente.post("/api/v1/bloqueos", json=datos_bloqueo(**cambios))
    assert r.status_code == 201, r.text
    return r.json()
