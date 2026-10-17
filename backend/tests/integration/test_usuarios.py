"""Gestión de usuarios por el administrador (U-12, U-13, U-15, U-17, RU-03 a RU-05, RU-09)."""

import pytest
from sqlalchemy import select

from app.core.errores import ReglaDeNegocio
from app.modulos.auditoria.modelos import RegistroAuditoria
from app.modulos.usuarios import servicio
from app.modulos.usuarios.esquemas import UsuarioEditar
from app.modulos.usuarios.modelos import Rol
from tests.integration.ayudas import CONTRASENA, crear_usuario, ingresar

pytestmark = pytest.mark.integracion


@pytest.fixture
def admin(sesion_bd):
    return crear_usuario(sesion_bd, "admin", Rol.ADMINISTRADOR)


@pytest.fixture
def cliente_admin(nuevo_cliente, admin):
    cliente = nuevo_cliente()
    assert ingresar(cliente, "admin").status_code == 200
    return cliente


def nuevo(**cambios):
    datos = {
        "nombre_usuario": "Luis_Gomez",
        "nombre": "Luis Gómez",
        "correo": "Luis@Correo.com",
        "rol": "empleado",
        "contrasena_temporal": "temporal-12345",
    }
    return datos | cambios


def test_crear_usuario_normaliza_y_exige_cambio_de_contrasena(cliente_admin, nuevo_cliente):
    r = cliente_admin.post("/api/v1/usuarios", json=nuevo())
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["nombre_usuario"] == "luis_gomez"
    assert cuerpo["correo"] == "luis@correo.com"
    assert cuerpo["debe_cambiar_contrasena"] is True
    assert "hash_contrasena" not in cuerpo and "contrasena_temporal" not in cuerpo

    assert ingresar(nuevo_cliente(), "luis_gomez", "temporal-12345").json()[
        "debe_cambiar_contrasena"
    ]


def test_u12_nombre_de_usuario_duplicado_sin_importar_mayusculas(cliente_admin):
    cliente_admin.post("/api/v1/usuarios", json=nuevo())
    r = cliente_admin.post("/api/v1/usuarios", json=nuevo(nombre_usuario="LUIS_GOMEZ"))
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "usuario_duplicado"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nombre_usuario", "ab"),
        ("nombre_usuario", "con espacio"),
        ("nombre_usuario", "josé"),
        ("correo", "sin-arroba"),
        ("rol", "superusuario"),
        ("contrasena_temporal", "corta"),
        ("contrasena_temporal", "luis_gomez"),
        ("campo_extra", "x"),
    ],
)
def test_datos_invalidos_se_rechazan_con_422(cliente_admin, campo, valor):
    r = cliente_admin.post("/api/v1/usuarios", json=nuevo(**{campo: valor}))
    assert r.status_code == 422, r.text


def test_editar_cambia_solo_lo_enviado_y_audita_antes_y_despues(cliente_admin, sesion_bd):
    usuario_id = cliente_admin.post("/api/v1/usuarios", json=nuevo()).json()["id"]
    r = cliente_admin.patch(f"/api/v1/usuarios/{usuario_id}", json={"nombre": "Luis G."})
    assert r.status_code == 200
    assert r.json()["nombre"] == "Luis G."
    assert r.json()["correo"] == "luis@correo.com"

    registro = sesion_bd.scalars(
        select(RegistroAuditoria)
        .where(RegistroAuditoria.accion == "usuario.editar")
        .order_by(RegistroAuditoria.id.desc())
    ).first()
    assert registro.valor_anterior == {"nombre": "Luis Gómez"}
    assert registro.valor_nuevo == {"nombre": "Luis G."}
    assert registro.entidad_id == str(usuario_id)


def test_editar_no_admite_nulos_en_campos_obligatorios(cliente_admin, admin):
    r = cliente_admin.patch(f"/api/v1/usuarios/{admin.id}", json={"nombre": None})
    assert r.status_code == 422


def test_u15_cambiar_rol_cierra_las_sesiones_del_usuario(cliente_admin, nuevo_cliente, sesion_bd):
    empleado = crear_usuario(sesion_bd, "carla")
    cliente = nuevo_cliente()
    ingresar(cliente, "carla")

    r = cliente_admin.patch(f"/api/v1/usuarios/{empleado.id}", json={"rol": "administrador"})
    assert r.status_code == 200
    assert cliente.get("/api/v1/auth/yo").status_code == 401


def test_u13_el_ultimo_administrador_activo_no_puede_desactivarse_ni_degradarse(
    sesion_bd, admin, reloj
):
    # Por la API, RU-05 ya impide que el último administrador se desactive a sí mismo; aquí se
    # prueba la regla del servicio directamente, como la vería una petición concurrente.
    otro = crear_usuario(sesion_bd, "segunda", Rol.ADMINISTRADOR)
    servicio.desactivar(sesion_bd, otro.id, actor_id=admin.id, ip=None, ahora=reloj())

    with pytest.raises(ReglaDeNegocio) as error:
        servicio.editar(
            sesion_bd,
            admin.id,
            UsuarioEditar(rol=Rol.EMPLEADO),
            actor_id=otro.id,
            ip=None,
            ahora=reloj(),
        )
    assert error.value.codigo == "ultimo_administrador"
    with pytest.raises(ReglaDeNegocio) as error:
        servicio.desactivar(sesion_bd, admin.id, actor_id=otro.id, ip=None, ahora=reloj())
    assert error.value.codigo == "ultimo_administrador"


def test_ru05_un_administrador_no_puede_desactivarse_ni_cambiarse_el_rol(cliente_admin, admin):
    r = cliente_admin.post(f"/api/v1/usuarios/{admin.id}/desactivar")
    assert r.status_code == 409
    assert r.json()["error"]["codigo"] == "accion_sobre_si_mismo"
    r = cliente_admin.patch(f"/api/v1/usuarios/{admin.id}", json={"rol": "empleado"})
    assert r.json()["error"]["codigo"] == "accion_sobre_si_mismo"


def test_ru03_desactivar_y_reactivar_conserva_el_usuario(cliente_admin, sesion_bd, nuevo_cliente):
    empleado = crear_usuario(sesion_bd, "carla")
    assert (
        cliente_admin.post(f"/api/v1/usuarios/{empleado.id}/desactivar").json()["activo"] is False
    )
    assert cliente_admin.get("/api/v1/usuarios?activo=false").json()[0]["nombre_usuario"] == "carla"
    assert cliente_admin.post(f"/api/v1/usuarios/{empleado.id}/activar").json()["activo"] is True
    assert ingresar(nuevo_cliente(), "carla").status_code == 200


def test_ru09_restablecer_contrasena(cliente_admin, sesion_bd, nuevo_cliente):
    empleado = crear_usuario(sesion_bd, "carla")
    cliente = nuevo_cliente()
    ingresar(cliente, "carla")

    r = cliente_admin.post(
        f"/api/v1/usuarios/{empleado.id}/restablecer-contrasena",
        json={"contrasena_temporal": "temporal-98765"},
    )
    assert r.status_code == 200
    assert r.json()["debe_cambiar_contrasena"] is True
    assert cliente.get("/api/v1/auth/yo").status_code == 401  # U-15
    assert ingresar(nuevo_cliente(), "carla", CONTRASENA).status_code == 401
    assert ingresar(nuevo_cliente(), "carla", "temporal-98765").status_code == 200


def test_restablecer_desbloquea_una_cuenta_bloqueada(cliente_admin, sesion_bd, nuevo_cliente):
    empleado = crear_usuario(sesion_bd, "carla")
    for _ in range(5):
        ingresar(nuevo_cliente(), "carla", "mala-contrasena")
    cliente_admin.post(
        f"/api/v1/usuarios/{empleado.id}/restablecer-contrasena",
        json={"contrasena_temporal": "temporal-98765"},
    )
    assert ingresar(nuevo_cliente(), "carla", "temporal-98765").status_code == 200


def test_usuario_inexistente_responde_404(cliente_admin):
    assert cliente_admin.get("/api/v1/usuarios/99999").status_code == 404
    assert cliente_admin.post("/api/v1/usuarios/99999/desactivar").status_code == 404


def test_listar_filtra_por_rol(cliente_admin, sesion_bd):
    crear_usuario(sesion_bd, "carla")
    nombres = [
        u["nombre_usuario"] for u in cliente_admin.get("/api/v1/usuarios?rol=empleado").json()
    ]
    assert nombres == ["carla"]


def test_u17_cada_operacion_queda_auditada_sin_contrasenas(cliente_admin, sesion_bd, admin):
    usuario_id = cliente_admin.post("/api/v1/usuarios", json=nuevo()).json()["id"]
    cliente_admin.patch(f"/api/v1/usuarios/{usuario_id}", json={"rol": "administrador"})
    cliente_admin.post(f"/api/v1/usuarios/{usuario_id}/desactivar")
    cliente_admin.post(f"/api/v1/usuarios/{usuario_id}/activar")
    cliente_admin.post(
        f"/api/v1/usuarios/{usuario_id}/restablecer-contrasena",
        json={"contrasena_temporal": "temporal-98765"},
    )

    registros = sesion_bd.scalars(
        select(RegistroAuditoria)
        .where(RegistroAuditoria.entidad_id == str(usuario_id))
        .order_by(RegistroAuditoria.id)
    ).all()
    assert [r.accion for r in registros] == [
        "usuario.crear",
        "usuario.editar",
        "usuario.desactivar",
        "usuario.activar",
        "usuario.restablecer_contrasena",
    ]
    for registro in registros:
        assert registro.usuario_id == admin.id
        assert registro.ip == "testclient"
        assert registro.momento is not None
        texto = str(registro.valor_anterior) + str(registro.valor_nuevo)
        assert "temporal-" not in texto and "argon2" not in texto
