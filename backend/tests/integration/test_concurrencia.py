"""Transacciones reales con conexiones separadas (I1, I3, M11).

A diferencia del resto de pruebas, estas confirman datos de verdad, porque solo así se
reproducen los bloqueos entre peticiones simultáneas. Los usuarios que crean quedan
desactivados al final para no afectar a otras pruebas (no se pueden borrar: la auditoría
los referencia).
"""

import threading
from datetime import UTC, datetime

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy import select, text, update

from app.api.dependencias import BD
from app.core.config import Configuracion
from app.core.errores import ErrorAplicacion, ReglaDeNegocio
from app.db.sesion import crear_fabrica
from app.main import crear_app
from app.modulos.usuarios import servicio
from app.modulos.usuarios.esquemas import UsuarioCrear
from app.modulos.usuarios.modelos import Rol, Usuario

pytestmark = pytest.mark.integracion
PREFIJO = "conc_"
AHORA = datetime(2026, 10, 17, 15, 0, tzinfo=UTC)


@pytest.fixture
def fabrica(motor_pruebas):
    fabrica = crear_fabrica(motor_pruebas)
    yield fabrica
    with motor_pruebas.begin() as conexion:
        conexion.execute(
            update(Usuario).where(Usuario.nombre_usuario.startswith(PREFIJO)).values(activo=False)
        )


def crear_confirmado(fabrica, nombre_usuario: str, rol: Rol) -> int:
    with fabrica() as bd:
        usuario = servicio.crear(
            bd,
            UsuarioCrear(
                nombre_usuario=nombre_usuario,
                nombre="Zz prueba de concurrencia",
                rol=rol,
                contrasena_temporal="contrasena-segura-1",
            ),
            actor_id=None,
            ip=None,
            debe_cambiar_contrasena=False,
        )
        bd.commit()
        return usuario.id


def test_i3_dos_administradores_que_se_desactivan_a_la_vez_no_se_bloquean(fabrica, motor_pruebas):
    # Se desactivan los administradores de otras pruebas para que estos dos sean los únicos.
    with motor_pruebas.begin() as conexion:
        conexion.execute(
            update(Usuario).where(Usuario.rol == Rol.ADMINISTRADOR).values(activo=False)
        )
    a = crear_confirmado(fabrica, f"{PREFIJO}a", Rol.ADMINISTRADOR)
    b = crear_confirmado(fabrica, f"{PREFIJO}b", Rol.ADMINISTRADOR)

    salida = threading.Barrier(2)
    resultados: dict[str, object] = {}

    def desactivar(objetivo: int, actor: int, clave: str) -> None:
        with fabrica() as bd:
            salida.wait()
            try:
                servicio.desactivar(bd, objetivo, actor_id=actor, ip=None, ahora=AHORA)
                bd.commit()
                resultados[clave] = "ok"
            except Exception as error:  # noqa: BLE001 - se examina abajo
                resultados[clave] = error

    hilos = [
        threading.Thread(target=desactivar, args=(b, a, "a_desactiva_b")),
        threading.Thread(target=desactivar, args=(a, b, "b_desactiva_a")),
    ]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=20)

    valores = list(resultados.values())
    assert valores.count("ok") == 1, resultados
    rechazo = next(v for v in valores if v != "ok")
    assert isinstance(rechazo, ReglaDeNegocio), repr(rechazo)
    assert rechazo.codigo == "ultimo_administrador"
    with fabrica() as bd:
        activos = bd.scalars(
            select(Usuario.id).where(Usuario.id.in_([a, b]), Usuario.activo.is_(True))
        ).all()
    assert len(activos) == 1


def test_i1_si_el_caso_de_uso_falla_no_queda_nada_guardado(url_pruebas, motor_pruebas):
    """Un endpoint que usa un servicio y luego falla no deja datos a medias (RNF-06)."""
    app = crear_app(Configuracion(entorno="pruebas", database_url=url_pruebas))
    router = APIRouter()

    @router.post("/api/v1/prueba/a-medias")
    def a_medias(bd: BD):
        servicio.crear(
            bd,
            UsuarioCrear(
                nombre_usuario=f"{PREFIJO}a_medias",
                nombre="Zz a medias",
                rol=Rol.EMPLEADO,
                contrasena_temporal="contrasena-segura-1",
            ),
            actor_id=None,
            ip=None,
        )
        raise ReglaDeNegocio("Falla un paso posterior del mismo caso de uso.")

    app.include_router(router)
    with TestClient(app, raise_server_exceptions=False) as cliente:
        assert cliente.post("/api/v1/prueba/a-medias").status_code == 409

    with motor_pruebas.connect() as conexion:
        existe = conexion.execute(
            text("SELECT count(*) FROM usuarios WHERE nombre_usuario = :n"),
            {"n": f"{PREFIJO}a_medias"},
        ).scalar()
        auditado = conexion.execute(
            text("SELECT count(*) FROM auditoria WHERE valor_nuevo->>'nombre_usuario' = :n"),
            {"n": f"{PREFIJO}a_medias"},
        ).scalar()
    assert (existe, auditado) == (0, 0)


def test_i1_nombre_duplicado_concurrente_es_regla_de_negocio(fabrica, monkeypatch):
    crear_confirmado(fabrica, f"{PREFIJO}dup", Rol.EMPLEADO)
    # Simula la carrera: la verificación previa no lo ve, pero la restricción única sí.
    monkeypatch.setattr(servicio.repositorio, "existe_nombre_usuario", lambda *a, **k: False)
    with fabrica() as bd, pytest.raises(ErrorAplicacion) as error:
        servicio.crear(
            bd,
            UsuarioCrear(
                nombre_usuario=f"{PREFIJO}dup",
                nombre="Zz duplicado",
                rol=Rol.EMPLEADO,
                contrasena_temporal="contrasena-segura-1",
            ),
            actor_id=None,
            ip=None,
        )
    assert error.value.codigo == "usuario_duplicado"
