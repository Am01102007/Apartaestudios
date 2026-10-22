"""Bloqueos con transacciones reales en conexiones separadas (R-06 y base de CA-03).

Confirman datos de verdad, con documentos propios (99000000x) que no usa ninguna otra prueba.
"""

import threading
import time
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select, update

from app.core.errores import ReglaDeNegocio
from app.db.sesion import crear_fabrica
from app.modulos.bloqueos import repositorio, servicio
from app.modulos.bloqueos.esquemas import BloqueoCrear
from app.modulos.bloqueos.modelos import Bloqueo
from app.modulos.usuarios import servicio as usuarios
from app.modulos.usuarios.esquemas import UsuarioCrear
from app.modulos.usuarios.modelos import Rol, Usuario
from tests.integration.ayudas import en_paralelo

pytestmark = pytest.mark.integracion
AHORA = datetime(2026, 10, 22, 15, 0, tzinfo=UTC)


@pytest.fixture
def fabrica(motor_pruebas):
    fabrica = crear_fabrica(motor_pruebas)
    yield fabrica
    with motor_pruebas.begin() as conexion:
        conexion.execute(
            update(Usuario).where(Usuario.nombre_usuario == "conc_bloqueos").values(activo=False)
        )


@pytest.fixture
def admin_id(fabrica):
    with fabrica() as bd:
        existente = bd.scalar(select(Usuario.id).where(Usuario.nombre_usuario == "conc_bloqueos"))
        if existente:
            return existente
        admin = usuarios.crear(
            bd,
            UsuarioCrear(
                nombre_usuario="conc_bloqueos",
                nombre="Zz bloqueos",
                rol=Rol.ADMINISTRADOR,
                contrasena_temporal="contrasena-segura-1",
            ),
            actor_id=None,
            ip=None,
        )
        bd.commit()
        return admin.id


def _bloquear(fabrica, admin_id, numero):
    def tarea():
        with fabrica() as bd:
            servicio.bloquear(
                bd,
                BloqueoCrear(
                    tipo_documento="CC", numero_documento=numero, nombre="Zz", motivo="Prueba"
                ),
                actor_id=admin_id,
                ip=None,
                ahora=AHORA,
            )
            bd.commit()

    return tarea


def _activos(fabrica, numero) -> int:
    with fabrica() as bd:
        return bd.scalar(
            select(func.count())
            .select_from(Bloqueo)
            .where(Bloqueo.numero_documento == numero, Bloqueo.levantado_en.is_(None))
        )


def test_r06_dos_bloqueos_simultaneos_del_mismo_documento(fabrica, admin_id):
    resultados = en_paralelo(*[_bloquear(fabrica, admin_id, "990000001")] * 2)
    assert resultados.count("ok") == 1, resultados
    rechazo = next(r for r in resultados if r != "ok")
    assert isinstance(rechazo, ReglaDeNegocio) and rechazo.codigo == "ya_bloqueado"
    assert _activos(fabrica, "990000001") == 1


def test_r06_el_indice_unico_respalda_la_regla(fabrica, admin_id, monkeypatch):
    # Sin el bloqueo del documento, las dos pasan la verificación previa a la vez: solo el
    # índice único parcial puede detener a la segunda.
    monkeypatch.setattr(repositorio, "bloquear_documento", lambda *a, **k: None)
    salida = threading.Barrier(2)
    original = repositorio.activo_de

    def activo_de_a_la_vez(*args, **kwargs):
        resultado = original(*args, **kwargs)
        salida.wait(timeout=10)
        return resultado

    monkeypatch.setattr(repositorio, "activo_de", activo_de_a_la_vez)
    resultados = en_paralelo(*[_bloquear(fabrica, admin_id, "990000002")] * 2)
    assert resultados.count("ok") == 1, resultados
    rechazo = next(r for r in resultados if r != "ok")
    assert isinstance(rechazo, ReglaDeNegocio) and rechazo.codigo == "ya_bloqueado"


def test_ca03_base_la_verificacion_espera_a_un_bloqueo_en_curso(fabrica, admin_id, monkeypatch):
    """Lo que hará el módulo de contratos: si alguien está bloqueando el documento, la
    verificación espera a que termine y entonces ve el bloqueo."""
    bloqueando = threading.Event()
    continuar = threading.Event()
    verificacion_terminada = threading.Event()
    original = repositorio.activo_de

    def activo_de_despacio(*args, **kwargs):
        resultado = original(*args, **kwargs)
        if threading.current_thread().name == "bloquear":
            bloqueando.set()  # ya tiene el bloqueo del documento
            continuar.wait(timeout=10)
        return resultado

    monkeypatch.setattr(repositorio, "activo_de", activo_de_despacio)

    def verificar():
        bloqueando.wait(timeout=10)
        try:
            with fabrica() as bd:
                servicio.exigir_sin_bloqueo(bd, "CC", "990000003")
        finally:
            verificacion_terminada.set()

    def soltar():
        bloqueando.wait(timeout=10)
        time.sleep(0.5)
        assert not verificacion_terminada.is_set(), "la verificación no esperó"
        continuar.set()

    tarea_bloquear = _bloquear(fabrica, admin_id, "990000003")

    def bloquear():
        threading.current_thread().name = "bloquear"
        tarea_bloquear()

    resultados = en_paralelo(bloquear, verificar, soltar)
    assert resultados[0] == "ok" and resultados[2] == "ok", resultados
    assert isinstance(resultados[1], ReglaDeNegocio), resultados
    assert resultados[1].codigo == "persona_bloqueada"
