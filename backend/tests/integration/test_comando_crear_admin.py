import pytest
from sqlalchemy import select

from app.comandos import crear_admin
from app.core.seguridad import verificar_contrasena
from app.modulos.usuarios.modelos import Usuario

pytestmark = pytest.mark.integracion


@pytest.fixture(autouse=True)
def usar_base_de_pruebas(monkeypatch, sesion_bd):
    monkeypatch.setattr(crear_admin, "abrir_sesion", lambda: sesion_bd)
    monkeypatch.setenv("APP_CONTRASENA_ADMIN", "clave-inicial-123")


def test_crea_un_administrador_activo_sin_cambio_pendiente(sesion_bd, capsys):
    codigo = crear_admin.main(["--usuario", "Maryam", "--nombre", "Maryam"])

    assert codigo == 0
    usuario = sesion_bd.scalar(select(Usuario).where(Usuario.nombre_usuario == "maryam"))
    assert usuario.rol == "administrador"
    assert usuario.activo and not usuario.debe_cambiar_contrasena
    assert verificar_contrasena(usuario.hash_contrasena, "clave-inicial-123")
    assert "creado" in capsys.readouterr().out


def test_rechaza_un_usuario_repetido_o_invalido(capsys):
    assert crear_admin.main(["--usuario", "maryam", "--nombre", "Maryam"]) == 0
    assert crear_admin.main(["--usuario", "MARYAM", "--nombre", "Otra"]) == 1
    assert crear_admin.main(["--usuario", "a b", "--nombre", "Otra"]) == 1
    assert "ya está registrado" in capsys.readouterr().err
