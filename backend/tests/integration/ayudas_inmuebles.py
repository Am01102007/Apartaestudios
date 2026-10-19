"""Datos de ejemplo para las pruebas de propietarios y apartaestudios."""

from fastapi.testclient import TestClient


def datos_propietario(**cambios) -> dict:
    return {
        "nombre": "Ana Ruiz",
        "tipo_documento": "CC",
        "numero_documento": "1.234.567",
        "telefono": "+57 300 123 4567",
        "correo": "Ana@Correo.com",
    } | cambios


def datos_apartaestudio(propietario_id: int, **cambios) -> dict:
    return {
        "codigo": "201",
        "propietario_id": propietario_id,
        "direccion": "Calle 10 # 5-20",
        "area_m2": "28.50",
    } | cambios


def crear_propietario(cliente: TestClient, **cambios) -> dict:
    r = cliente.post("/api/v1/propietarios", json=datos_propietario(**cambios))
    assert r.status_code == 201, r.text
    return r.json()


def crear_apartaestudio(cliente: TestClient, propietario_id: int, **cambios) -> dict:
    r = cliente.post("/api/v1/apartaestudios", json=datos_apartaestudio(propietario_id, **cambios))
    assert r.status_code == 201, r.text
    return r.json()
