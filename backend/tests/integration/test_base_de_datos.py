import pytest
from sqlalchemy import text

from alembic import command
from tests.conftest import config_alembic

pytestmark = pytest.mark.integracion


def test_salud_con_base_de_datos_real(cliente_bd):
    r = cliente_bd.get("/api/v1/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok", "base_de_datos": "ok"}


def test_migraciones_instalan_btree_gist(sesion_bd):
    instalada = sesion_bd.execute(
        text("SELECT 1 FROM pg_extension WHERE extname = 'btree_gist'")
    ).scalar()
    assert instalada == 1


def test_migraciones_se_revierten_y_reaplican(motor_pruebas, url_pruebas):
    config = config_alembic(url_pruebas)
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    with motor_pruebas.connect() as conexion:
        version = conexion.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert version == "0001"


def test_conexion_trabaja_en_utc(sesion_bd):
    assert sesion_bd.execute(text("SHOW timezone")).scalar() == "UTC"
