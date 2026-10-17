"""Fijaciones comunes de las pruebas.

Las pruebas de integración usan la base APP_DATABASE_URL_PRUEBAS, que se vacía y se migra
desde cero en cada ejecución. Nunca apuntes esa variable a la base de desarrollo o
producción.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from app.core.config import Configuracion, obtener_configuracion
from app.db.sesion import crear_motor, obtener_sesion
from app.main import crear_app

RAIZ_BACKEND = Path(__file__).resolve().parents[1]


def config_alembic(url: str) -> Config:
    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    return config


@pytest.fixture
def app():
    return crear_app(Configuracion(entorno="pruebas"))


@pytest.fixture
def cliente(app) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="session")
def url_pruebas() -> str:
    url = obtener_configuracion().database_url_pruebas
    if not url.rsplit("/", 1)[-1].endswith("_test"):
        pytest.exit("APP_DATABASE_URL_PRUEBAS debe apuntar a una base cuyo nombre termine en _test")
    return url


@pytest.fixture(scope="session")
def motor_pruebas(url_pruebas) -> Iterator[Engine]:
    motor = crear_motor(url_pruebas)
    with motor.begin() as conexion:
        conexion.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    command.upgrade(config_alembic(url_pruebas), "head")
    yield motor
    motor.dispose()


@pytest.fixture
def sesion_bd(motor_pruebas) -> Iterator[Session]:
    """Sesión dentro de una transacción que se revierte al final de cada prueba."""
    conexion = motor_pruebas.connect()
    transaccion = conexion.begin()
    sesion = sessionmaker(bind=conexion, join_transaction_mode="create_savepoint")()
    try:
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()


@pytest.fixture
def cliente_bd(app, sesion_bd) -> Iterator[TestClient]:
    app.dependency_overrides[obtener_sesion] = lambda: sesion_bd
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
