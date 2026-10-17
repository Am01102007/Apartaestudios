"""Pruebas de las correcciones de la revisión del módulo 1 que no necesitan base de datos."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from app.core import limite
from app.core.config import Configuracion
from app.core.limite import LimiteVentana
from app.db.permisos import sql_permisos
from app.main import crear_app
from app.modulos.auditoria.servicio import _limpiar
from app.modulos.usuarios.modelos import Rol

AHORA = datetime(2026, 10, 17, 15, 0, tzinfo=UTC)


def test_i2_auditoria_convierte_montos_decimal_y_estructuras_anidadas():
    limpio = _limpiar(
        {
            "valor": Decimal("850000"),
            "periodo": {"inicio": date(2026, 1, 31), "rol": Rol.EMPLEADO},
            "aplicaciones": [{"monto": Decimal("1.50"), "hash_contrasena": "x"}],
            "contrasena": "secreta",
        }
    )
    assert limpio == {
        "valor": "850000",
        "periodo": {"inicio": "2026-01-31", "rol": "empleado"},
        "aplicaciones": [{"monto": "1.50"}],
    }


class _ErrorPostgres(Exception):
    def __init__(self, sqlstate: str):
        self.sqlstate = sqlstate


@pytest.mark.parametrize(("sqlstate", "estado"), [("40P01", 409), ("40001", 409), ("08006", 500)])
def test_i3_bloqueo_mutuo_o_serializacion_responden_409(sqlstate, estado):
    app = crear_app(Configuracion(entorno="pruebas"))
    router = APIRouter()

    @router.get("/api/v1/prueba/concurrencia")
    def concurrencia():
        raise OperationalError("UPDATE ...", {}, _ErrorPostgres(sqlstate))

    app.include_router(router)
    with TestClient(app, raise_server_exceptions=False) as cliente:
        r = cliente.get("/api/v1/prueba/concurrencia")
    assert r.status_code == estado
    if estado == 409:
        assert r.json()["error"]["codigo"] == "conflicto_concurrente"


def test_i5_sin_entorno_declarado_se_asume_produccion(monkeypatch):
    monkeypatch.delenv("APP_ENTORNO", raising=False)
    monkeypatch.delenv("APP_CLAVE_JWT", raising=False)
    with pytest.raises(ValidationError, match="APP_CLAVE_JWT"):
        Configuracion(_env_file=None)
    assert Configuracion(_env_file=None, clave_jwt="k" * 40).es_produccion


def test_m9_hsts_solo_en_produccion():
    with TestClient(crear_app(Configuracion(entorno="produccion", clave_jwt="k" * 40))) as c:
        assert "max-age=" in c.get("/api/v1/no-existe").headers["Strict-Transport-Security"]
    with TestClient(crear_app(Configuracion(entorno="pruebas"))) as c:
        assert "Strict-Transport-Security" not in c.get("/api/v1/no-existe").headers


def test_m1_cada_aplicacion_usa_su_propia_base_de_datos():
    app = crear_app(
        Configuracion(entorno="pruebas", database_url="postgresql+psycopg://u:p@otro:5432/x")
    )
    assert app.state.fabrica_sesiones.kw["bind"].url.host == "otro"


def test_m6_el_limite_olvida_las_ip_inactivas(monkeypatch):
    monkeypatch.setattr(limite, "MAXIMO_CLAVES_ANTES_DE_LIMPIAR", 3)
    contador = LimiteVentana(5, timedelta(minutes=1))
    for i in range(4):
        contador.permitir(f"ip-{i}", AHORA)
    assert contador.claves == 4
    contador.permitir("ip-nueva", AHORA + timedelta(minutes=2))
    assert contador.claves == 1


def test_i4_sql_de_permisos_rechaza_nombres_de_rol_peligrosos():
    assert "apartaestudios_app" in sql_permisos("apartaestudios_app")
    for rol in ("app; DROP TABLE usuarios", "App", "", "a b"):
        with pytest.raises(ValueError):
            sql_permisos(rol)
