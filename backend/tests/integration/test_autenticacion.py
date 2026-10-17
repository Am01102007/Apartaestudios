"""Inicio y cierre de sesión, expiración, bloqueo y CSRF (U-01 a U-08, U-14, U-16)."""

import pytest
from sqlalchemy import select

from app.modulos.auditoria.modelos import RegistroAuditoria
from app.modulos.usuarios.modelos import Rol, Usuario
from tests.integration.ayudas import CONTRASENA, crear_usuario, ingresar

pytestmark = pytest.mark.integracion


@pytest.fixture
def empleado(sesion_bd):
    return crear_usuario(sesion_bd, "ana.perez")


def test_u01_ingreso_correcto_crea_cookies_sin_token_en_el_cuerpo(cliente_bd, empleado):
    r = ingresar(cliente_bd, "ana.perez")

    assert r.status_code == 200
    assert r.json() == {
        "id": empleado.id,
        "nombre_usuario": "ana.perez",
        "nombre": "Ana.Perez",
        "rol": "empleado",
        "debe_cambiar_contrasena": False,
    }
    assert "sesion" in r.cookies and "csrf_token" in r.cookies
    assert r.cookies["sesion"] not in r.text
    assert cliente_bd.get("/api/v1/auth/yo").json()["nombre_usuario"] == "ana.perez"


def test_u01_el_nombre_de_usuario_no_distingue_mayusculas(cliente_bd, empleado):
    assert ingresar(cliente_bd, "  ANA.Perez ").status_code == 200


def test_u01_cookies_con_atributos_de_seguridad(nuevo_cliente, empleado, app):
    app.state.configuracion = app.state.configuracion.model_copy(update={"cookie_segura": True})
    r = nuevo_cliente().post(
        "/api/v1/auth/login", json={"nombre_usuario": "ana.perez", "contrasena": CONTRASENA}
    )
    cookies = {c.split("=", 1)[0]: c.lower() for c in r.headers.get_list("set-cookie")}
    assert "httponly" in cookies["sesion"]
    assert "secure" in cookies["sesion"]
    assert "samesite=strict" in cookies["sesion"]
    assert "path=/api" in cookies["sesion"]
    assert "httponly" not in cookies["csrf_token"]
    assert "secure" in cookies["csrf_token"]


@pytest.mark.parametrize(
    ("usuario", "contrasena"), [("ana.perez", "otra-contrasena-1"), ("no.existe", CONTRASENA)]
)
def test_u02_credenciales_incorrectas_responden_igual(cliente_bd, empleado, usuario, contrasena):
    r = ingresar(cliente_bd, usuario, contrasena)
    assert r.status_code == 401
    assert r.json()["error"] == {
        "codigo": "credenciales_invalidas",
        "mensaje": "Usuario o contraseña incorrectos.",
        "detalles": [],
    }
    assert "sesion" not in r.cookies


def test_u03_cinco_fallos_bloquean_quince_minutos(cliente_bd, empleado, reloj):
    for _ in range(5):
        assert ingresar(cliente_bd, "ana.perez", "mala-contrasena").status_code == 401

    r = ingresar(cliente_bd, "ana.perez")
    assert r.status_code == 401
    assert r.json()["error"]["codigo"] == "cuenta_bloqueada"

    reloj.avanzar(minutes=14, seconds=59)
    assert ingresar(cliente_bd, "ana.perez").status_code == 401

    reloj.avanzar(seconds=1)
    assert ingresar(cliente_bd, "ana.perez").status_code == 200


def test_u03_un_ingreso_correcto_reinicia_el_contador(cliente_bd, empleado, sesion_bd):
    for _ in range(4):
        ingresar(cliente_bd, "ana.perez", "mala-contrasena")
    assert ingresar(cliente_bd, "ana.perez").status_code == 200
    sesion_bd.refresh(empleado)
    assert empleado.intentos_fallidos == 0
    assert ingresar(cliente_bd, "ana.perez", "mala-contrasena").status_code == 401
    assert ingresar(cliente_bd, "ana.perez").status_code == 200


def test_u05_cerrar_sesion_invalida_la_cookie_aunque_se_haya_copiado(nuevo_cliente, empleado):
    cliente = nuevo_cliente()
    ingresar(cliente, "ana.perez")
    copia = nuevo_cliente()
    copia.cookies.set("sesion", cliente.cookies["sesion"], path="/api")

    assert cliente.post("/api/v1/auth/logout").status_code == 204
    assert copia.get("/api/v1/auth/yo").status_code == 401
    assert cliente.get("/api/v1/auth/yo").status_code == 401


def test_u06_sesion_expira_tras_30_minutos_sin_uso(cliente_bd, empleado, reloj):
    ingresar(cliente_bd, "ana.perez")
    reloj.avanzar(minutes=29)
    assert cliente_bd.get("/api/v1/auth/yo").status_code == 200
    reloj.avanzar(minutes=29)  # el uso anterior renovó la sesión
    assert cliente_bd.get("/api/v1/auth/yo").status_code == 200
    reloj.avanzar(minutes=30)
    r = cliente_bd.get("/api/v1/auth/yo")
    assert r.status_code == 401
    assert r.json()["error"]["codigo"] == "sesion_expirada"


def test_u06_ninguna_sesion_dura_mas_de_12_horas(cliente_bd, empleado, reloj):
    ingresar(cliente_bd, "ana.perez")
    for _ in range(35):  # uso continuo cada 20 minutos hasta las 11 h 40 min
        reloj.avanzar(minutes=20)
        assert cliente_bd.get("/api/v1/auth/yo").status_code == 200
    reloj.avanzar(minutes=20)  # 12 horas exactas desde el ingreso
    assert cliente_bd.get("/api/v1/auth/yo").status_code == 401


def test_u06_token_alterado_se_rechaza(cliente_bd, empleado):
    ingresar(cliente_bd, "ana.perez")
    token = cliente_bd.cookies["sesion"]
    cliente_bd.cookies.set(
        "sesion", token[:-2] + ("aa" if token[-2:] != "aa" else "bb"), path="/api"
    )
    assert cliente_bd.get("/api/v1/auth/yo").status_code == 401


def test_u07_modificacion_sin_csrf_o_con_csrf_incorrecto_se_rechaza(cliente_bd, empleado):
    ingresar(cliente_bd, "ana.perez")
    token = cliente_bd.headers.pop("X-CSRF-Token")

    r = cliente_bd.post("/api/v1/auth/logout")
    assert r.status_code == 403
    assert r.json()["error"]["codigo"] == "csrf_invalido"

    cliente_bd.headers["X-CSRF-Token"] = "token-falso"
    assert cliente_bd.post("/api/v1/auth/logout").status_code == 403

    cliente_bd.headers["X-CSRF-Token"] = token
    assert cliente_bd.post("/api/v1/auth/logout").status_code == 204


def test_u04_usuario_desactivado_no_ingresa_y_pierde_sus_sesiones(
    nuevo_cliente, empleado, sesion_bd
):
    crear_usuario(sesion_bd, "admin", Rol.ADMINISTRADOR)
    admin = nuevo_cliente()
    ingresar(admin, "admin")
    cliente = nuevo_cliente()
    ingresar(cliente, "ana.perez")

    assert admin.post(f"/api/v1/usuarios/{empleado.id}/desactivar").status_code == 200

    assert cliente.get("/api/v1/auth/yo").status_code == 401
    r = ingresar(nuevo_cliente(), "ana.perez")
    assert r.status_code == 401
    assert r.json()["error"]["codigo"] == "usuario_inactivo"


def test_u14_cambiar_contrasena_exige_la_actual_y_cierra_las_otras_sesiones(
    nuevo_cliente, empleado
):
    principal, otra = nuevo_cliente(), nuevo_cliente()
    ingresar(principal, "ana.perez")
    ingresar(otra, "ana.perez")

    r = principal.post(
        "/api/v1/auth/cambiar-contrasena",
        json={"contrasena_actual": "equivocada-123", "contrasena_nueva": "nueva-contrasena-1"},
    )
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "contrasena_actual_incorrecta"

    r = principal.post(
        "/api/v1/auth/cambiar-contrasena",
        json={"contrasena_actual": CONTRASENA, "contrasena_nueva": "nueva-contrasena-1"},
    )
    assert r.status_code == 204
    assert principal.get("/api/v1/auth/yo").status_code == 200
    assert otra.get("/api/v1/auth/yo").status_code == 401
    assert ingresar(nuevo_cliente(), "ana.perez", "nueva-contrasena-1").status_code == 200
    assert ingresar(nuevo_cliente(), "ana.perez", CONTRASENA).status_code == 401


def test_u16_con_contrasena_temporal_solo_puede_cambiarla(nuevo_cliente, sesion_bd):
    crear_usuario(sesion_bd, "nuevo", debe_cambiar=True)
    crear_usuario(sesion_bd, "jefa", Rol.ADMINISTRADOR, debe_cambiar=True)
    cliente = nuevo_cliente()

    r = ingresar(cliente, "jefa")
    assert r.json()["debe_cambiar_contrasena"] is True
    assert cliente.get("/api/v1/auth/yo").status_code == 200
    r = cliente.get("/api/v1/usuarios")
    assert r.status_code == 403
    assert r.json()["error"]["codigo"] == "debe_cambiar_contrasena"

    cliente.post(
        "/api/v1/auth/cambiar-contrasena",
        json={"contrasena_actual": CONTRASENA, "contrasena_nueva": "definitiva-123"},
    )
    assert cliente.get("/api/v1/usuarios").status_code == 200
    assert cliente.get("/api/v1/auth/yo").json()["debe_cambiar_contrasena"] is False


def test_u10_contrasena_nueva_corta_o_igual_al_usuario_se_rechaza(cliente_bd, empleado):
    ingresar(cliente_bd, "ana.perez")
    for nueva in ("corta", "ANA.PEREZ"):
        r = cliente_bd.post(
            "/api/v1/auth/cambiar-contrasena",
            json={"contrasena_actual": CONTRASENA, "contrasena_nueva": nueva},
        )
        assert r.status_code == 422, nueva


def test_u09_hash_argon2id_y_nunca_expuesto(cliente_bd, empleado, sesion_bd):
    hash_guardado = sesion_bd.scalar(
        select(Usuario.hash_contrasena).where(Usuario.id == empleado.id)
    )
    assert hash_guardado.startswith("$argon2id$")
    assert CONTRASENA not in hash_guardado
    r = ingresar(cliente_bd, "ana.perez")
    assert "argon2" not in r.text and "hash" not in r.text


def test_ingresos_y_fallos_quedan_auditados(cliente_bd, empleado, sesion_bd):
    ingresar(cliente_bd, "ana.perez", "mala-contrasena")
    ingresar(cliente_bd, "fantasma", "mala-contrasena")
    ingresar(cliente_bd, "ana.perez")
    cliente_bd.post("/api/v1/auth/logout")

    acciones = sesion_bd.scalars(
        select(RegistroAuditoria.accion).order_by(RegistroAuditoria.id)
    ).all()
    assert acciones[-4:] == [
        "sesion.ingreso_fallido",
        "sesion.ingreso_fallido",
        "sesion.ingreso",
        "sesion.cierre",
    ]


def test_limite_de_intentos_por_ip(cliente_bd, empleado, app):
    app.state.limite_ingreso.maximo = 3
    for _ in range(3):
        ingresar(cliente_bd, "x", "y")
    r = ingresar(cliente_bd, "ana.perez")
    assert r.status_code == 429
    assert r.json()["error"]["codigo"] == "demasiadas_solicitudes"
