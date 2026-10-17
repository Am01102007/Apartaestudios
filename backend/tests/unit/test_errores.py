"""Formato único de errores (RNF-04) y cabeceras de seguridad."""

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.config import Configuracion
from app.core.errores import NoEncontrado, ReglaDeNegocio, SinPermiso
from app.main import crear_app


class Entrada(BaseModel):
    valor: int


@pytest.fixture
def cliente_errores(app):
    router = APIRouter(prefix="/api/v1/prueba")

    @router.get("/regla")
    def regla():
        raise ReglaDeNegocio("El apartaestudio ya tiene un contrato activo.", codigo="ocupado")

    @router.get("/permiso")
    def permiso():
        raise SinPermiso("Solo el administrador.")

    @router.get("/no-existe")
    def no_existe():
        raise NoEncontrado("Contrato no encontrado.")

    @router.post("/validacion")
    def validacion(entrada: Entrada):
        return entrada

    @router.get("/fallo")
    def fallo():
        raise RuntimeError("secreto interno")

    app.include_router(router)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_regla_de_negocio_devuelve_409_con_formato_unico(cliente_errores):
    r = cliente_errores.get("/api/v1/prueba/regla")
    assert r.status_code == 409
    assert r.json() == {
        "error": {
            "codigo": "ocupado",
            "mensaje": "El apartaestudio ya tiene un contrato activo.",
            "detalles": [],
        }
    }


@pytest.mark.parametrize(
    ("ruta", "estado", "codigo"),
    [
        ("/api/v1/prueba/permiso", 403, "sin_permiso"),
        ("/api/v1/prueba/no-existe", 404, "no_encontrado"),
    ],
)
def test_errores_de_aplicacion_usan_su_estado(cliente_errores, ruta, estado, codigo):
    r = cliente_errores.get(ruta)
    assert r.status_code == estado
    assert r.json()["error"]["codigo"] == codigo


def test_datos_invalidos_devuelven_422_con_el_campo(cliente_errores):
    r = cliente_errores.post("/api/v1/prueba/validacion", json={"valor": "abc"})
    assert r.status_code == 422
    error = r.json()["error"]
    assert error["codigo"] == "datos_invalidos"
    assert error["detalles"][0]["campo"] == "valor"


def test_ruta_inexistente_usa_el_formato_unico(cliente_errores):
    r = cliente_errores.get("/api/v1/no-hay-nada")
    assert r.status_code == 404
    assert r.json()["error"]["codigo"] == "no_encontrado"


def test_error_inesperado_no_revela_detalles_internos(cliente_errores):
    r = cliente_errores.get("/api/v1/prueba/fallo")
    assert r.status_code == 500
    assert r.json()["error"]["codigo"] == "error_interno"
    assert "secreto" not in r.text


def test_respuestas_incluyen_cabeceras_de_seguridad(cliente_errores):
    r = cliente_errores.get("/api/v1/no-hay-nada")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]


def test_documentacion_desactivada_en_produccion():
    with TestClient(crear_app(Configuracion(entorno="produccion", clave_jwt="k" * 40))) as c:
        assert c.get("/api/docs").status_code == 404
        assert c.get("/api/openapi.json").status_code == 404


def test_documentacion_disponible_fuera_de_produccion(cliente):
    assert cliente.get("/api/openapi.json").status_code == 200
