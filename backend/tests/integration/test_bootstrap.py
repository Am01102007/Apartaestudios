import pytest
from sqlalchemy import func, select

from app import bootstrap
from app.core.config import Configuracion
from app.modulos.usuarios.modelos import Usuario

pytestmark = pytest.mark.integracion


@pytest.fixture(autouse=True)
def usar_base_de_pruebas(monkeypatch, sesion_bd):
    monkeypatch.setattr(bootstrap, "abrir_sesion", lambda: sesion_bd)
    monkeypatch.setenv("APP_CONTRASENA_ADMIN", "clave-inicial-123")


def configurar(monkeypatch, **valores):
    config = Configuracion(entorno="pruebas", **valores)
    monkeypatch.setattr(bootstrap, "obtener_configuracion", lambda: config)


def test_crea_el_administrador_una_sola_vez(monkeypatch, sesion_bd, capsys):
    configurar(monkeypatch, admin_usuario="Admin", admin_nombre="Admin Inicial")

    assert bootstrap.main() == 0
    assert bootstrap.main() == 0  # cada despliegue lo repite sin duplicar

    total = sesion_bd.scalar(select(func.count()).where(Usuario.nombre_usuario == "admin"))
    assert total == 1
    assert "ya existe" in capsys.readouterr().out


def test_sin_variables_no_hace_nada(monkeypatch, sesion_bd):
    configurar(monkeypatch)
    assert bootstrap.main() == 0
    assert sesion_bd.scalar(select(func.count()).select_from(Usuario)) == 0


def test_contrasena_debil_falla_el_despliegue(monkeypatch):
    configurar(monkeypatch, admin_usuario="admin")
    monkeypatch.setenv("APP_CONTRASENA_ADMIN", "corta")
    assert bootstrap.main() == 1
