"""Fijaciones comunes de las pruebas.

Las pruebas de integración usan la base APP_DATABASE_URL_PRUEBAS, que se vacía y se migra
desde cero en cada ejecución. Nunca apuntes esa variable a la base de desarrollo o
producción.
"""

import os
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# La configuración por defecto es de producción; las pruebas declaran su entorno antes de
# importar la aplicación.
os.environ.setdefault("APP_ENTORNO", "pruebas")

from app.api.dependencias import obtener_reloj  # noqa: E402
from app.core.config import Configuracion, obtener_configuracion  # noqa: E402
from app.db.sesion import crear_motor, obtener_sesion  # noqa: E402
from app.main import crear_app  # noqa: E402

RAIZ_BACKEND = Path(__file__).resolve().parents[1]


def config_alembic(url: str) -> Config:
    config = Config(str(RAIZ_BACKEND / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    return config


class RelojPrueba:
    """Reloj controlable para simular el paso del tiempo (bloqueos, expiración)."""

    def __init__(self) -> None:
        self.momento = datetime(2026, 10, 17, 15, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.momento

    def avanzar(self, **kwargs) -> None:
        self.momento += timedelta(**kwargs)


@pytest.fixture
def reloj() -> RelojPrueba:
    return RelojPrueba()


@pytest.fixture
def config() -> Configuracion:
    # Las pruebas usan http://testserver, por eso la cookie no se marca Secure aquí.
    return Configuracion(entorno="pruebas", cookie_segura=False)


@pytest.fixture
def app(config, reloj):
    aplicacion = crear_app(config)
    aplicacion.dependency_overrides[obtener_reloj] = lambda: reloj
    return aplicacion


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
def nuevo_cliente(app, sesion_bd) -> Iterator[Callable[[], TestClient]]:
    """Fabrica clientes independientes (cada uno con sus cookies) sobre la base de pruebas."""

    def _sesion_compartida():
        # Como en producción: lo que la petición no confirmó se descarta al terminar.
        yield sesion_bd
        sesion_bd.rollback()

    app.dependency_overrides[obtener_sesion] = _sesion_compartida
    clientes: list[TestClient] = []

    def fabricar() -> TestClient:
        cliente = TestClient(app, raise_server_exceptions=False)
        clientes.append(cliente)
        return cliente

    yield fabricar
    for cliente in clientes:
        cliente.close()


@pytest.fixture
def cliente_bd(nuevo_cliente) -> TestClient:
    return nuevo_cliente()
