from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.core.config import Configuracion
from app.core.limite import LimiteVentana
from app.core.seguridad import (
    crear_jwt,
    generar_token,
    hashear_contrasena,
    leer_jwt,
    resumen_token,
    tokens_iguales,
    verificar_contrasena,
)

AHORA = datetime(2026, 10, 17, 15, 0, tzinfo=UTC)
CLAVE = "k" * 40


def test_hash_es_argon2id_con_sal_distinta_cada_vez():
    primero, segundo = hashear_contrasena("una-contrasena"), hashear_contrasena("una-contrasena")
    assert primero.startswith("$argon2id$")
    assert primero != segundo
    assert verificar_contrasena(primero, "una-contrasena")
    assert not verificar_contrasena(primero, "otra-contrasena")


def test_verificar_sin_hash_o_con_hash_danado_devuelve_falso():
    assert not verificar_contrasena(None, "x")
    assert not verificar_contrasena("no-es-un-hash", "x")


def test_jwt_valido_se_lee():
    token = crear_jwt(CLAVE, "sid-1", 7, AHORA, AHORA + timedelta(hours=1))
    assert leer_jwt(CLAVE, token, AHORA)["sid"] == "sid-1"


@pytest.mark.parametrize(
    ("clave", "momento"),
    [
        ("otra-clave-" * 4, AHORA),  # firma de otra clave
        (CLAVE, AHORA + timedelta(hours=1)),  # vencido
    ],
)
def test_jwt_con_otra_clave_o_vencido_se_rechaza(clave, momento):
    token = crear_jwt(CLAVE, "sid-1", 7, AHORA, AHORA + timedelta(hours=1))
    assert leer_jwt(clave, token, momento) is None


def test_jwt_sin_firma_se_rechaza():
    import jwt

    token = jwt.encode({"sub": "7", "sid": "s", "iat": AHORA, "exp": AHORA}, None, algorithm="none")
    assert leer_jwt(CLAVE, token, AHORA - timedelta(hours=1)) is None


def test_tokens_aleatorios_y_resumen():
    token = generar_token()
    assert len(token) >= 43 and token != generar_token()
    assert tokens_iguales(token, resumen_token(token))
    assert not tokens_iguales("otro", resumen_token(token))


def test_limite_por_ventana():
    limite = LimiteVentana(2, timedelta(minutes=1))
    assert limite.permitir("ip", AHORA)
    assert limite.permitir("ip", AHORA)
    assert not limite.permitir("ip", AHORA + timedelta(seconds=59))
    assert limite.permitir("otra-ip", AHORA)
    assert limite.permitir("ip", AHORA + timedelta(seconds=61))


def test_produccion_exige_clave_jwt_propia_y_cookie_segura():
    with pytest.raises(ValidationError):
        Configuracion(entorno="produccion")
    with pytest.raises(ValidationError):
        Configuracion(entorno="produccion", clave_jwt="corta")
    with pytest.raises(ValidationError):
        Configuracion(entorno="produccion", clave_jwt=CLAVE, cookie_segura=False)
    assert Configuracion(entorno="produccion", clave_jwt=CLAVE).es_produccion


def test_clave_jwt_corta_se_rechaza_en_cualquier_entorno():
    with pytest.raises(ValidationError):
        Configuracion(entorno="desarrollo", clave_jwt="")
