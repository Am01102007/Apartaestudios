"""Propietarios y apartaestudios con transacciones reales en conexiones separadas.

Como en test_concurrencia.py, estas pruebas confirman datos de verdad. Al final quedan
desactivados (no se pueden borrar: la auditoría los referencia) y usan nombres y códigos
propios para no cruzarse con otras pruebas.
"""

import threading
import time
from datetime import date

import pytest
from sqlalchemy import select, update

from app.core.errores import ReglaDeNegocio
from app.db.sesion import crear_fabrica
from app.modulos.inmuebles import apartaestudios, propietarios, repositorio
from app.modulos.inmuebles.esquemas import (
    ApartaestudioCrear,
    ApartaestudioEditar,
    PropietarioCrear,
)
from app.modulos.inmuebles.modelos import Apartaestudio, Propietario
from tests.integration.ayudas import en_paralelo

pytestmark = pytest.mark.integracion
PREFIJO = "CONC-"
HOY = date(2026, 10, 17)


@pytest.fixture
def fabrica(motor_pruebas):
    fabrica = crear_fabrica(motor_pruebas)
    yield fabrica
    with motor_pruebas.begin() as conexion:
        conexion.execute(
            update(Apartaestudio)
            .where(Apartaestudio.codigo.startswith(PREFIJO))
            .values(activo=False)
        )
        conexion.execute(
            update(Propietario).where(Propietario.nombre.startswith(PREFIJO)).values(activo=False)
        )


def nuevo_propietario(fabrica, documento: str) -> int:
    with fabrica() as bd:
        propietario = propietarios.crear(
            bd,
            PropietarioCrear(
                nombre=f"{PREFIJO}{documento}", tipo_documento="CC", numero_documento=documento
            ),
            actor_id=None,
            ip=None,
        )
        bd.commit()
        return propietario.id


def nuevo_apartaestudio(fabrica, codigo: str, propietario_id: int) -> int:
    with fabrica() as bd:
        apto = apartaestudios.crear(
            bd, _datos(codigo, propietario_id), actor_id=None, ip=None, hoy=HOY
        )
        bd.commit()
        return apto.id


def _datos(codigo: str, propietario_id: int) -> ApartaestudioCrear:
    return ApartaestudioCrear(
        codigo=codigo, propietario_id=propietario_id, direccion="Calle de prueba 1"
    )


def test_p05_dos_creaciones_simultaneas_con_el_mismo_codigo(fabrica, monkeypatch):
    # Con propietarios distintos, porque dos creaciones para el mismo propietario ya se
    # esperan una a otra en su bloqueo. Las dos pasan la verificación previa antes de que
    # ninguna inserte: solo la restricción única puede detener a la segunda.
    duenios = [nuevo_propietario(fabrica, "880000001"), nuevo_propietario(fabrica, "880000005")]
    salida = threading.Barrier(2)
    original = repositorio.existe_codigo

    def existe_codigo_a_la_vez(*args, **kwargs):
        resultado = original(*args, **kwargs)
        salida.wait(timeout=10)
        return resultado

    monkeypatch.setattr(repositorio, "existe_codigo", existe_codigo_a_la_vez)

    def crear(duenio):
        def tarea():
            with fabrica() as bd:
                apartaestudios.crear(
                    bd, _datos(f"{PREFIJO}DUP", duenio), actor_id=None, ip=None, hoy=HOY
                )
                bd.commit()

        return tarea

    resultados = en_paralelo(*(crear(d) for d in duenios))
    assert resultados.count("ok") == 1, resultados
    rechazo = next(r for r in resultados if r != "ok")
    assert isinstance(rechazo, ReglaDeNegocio) and rechazo.codigo == "codigo_duplicado", rechazo


def test_p10_desactivar_propietario_mientras_se_le_crea_un_apartaestudio(fabrica, monkeypatch):
    duenio = nuevo_propietario(fabrica, "880000002")
    contando = threading.Event()
    continuar = threading.Event()
    original = repositorio.contar_apartaestudios_activos

    def contar_despacio(*args, **kwargs):
        # La desactivación ya bloqueó al propietario; se detiene aquí mientras llega la creación.
        contando.set()
        continuar.wait(timeout=10)
        return original(*args, **kwargs)

    monkeypatch.setattr(repositorio, "contar_apartaestudios_activos", contar_despacio)
    creacion_terminada = threading.Event()

    def desactivar():
        with fabrica() as bd:
            propietarios.desactivar(bd, duenio, actor_id=None, ip=None)
            bd.commit()

    def crear():
        contando.wait(timeout=10)
        try:
            with fabrica() as bd:
                apartaestudios.crear(
                    bd, _datos(f"{PREFIJO}P10", duenio), actor_id=None, ip=None, hoy=HOY
                )
                bd.commit()
        finally:
            creacion_terminada.set()

    def soltar():
        contando.wait(timeout=10)
        time.sleep(0.5)
        # Sin el bloqueo del propietario, la creación ya habría terminado.
        assert not creacion_terminada.is_set()
        continuar.set()

    resultados = en_paralelo(desactivar, crear, soltar)
    assert resultados[0] == "ok" and resultados[2] == "ok", resultados
    assert isinstance(resultados[1], ReglaDeNegocio), resultados
    assert resultados[1].codigo == "propietario_no_valido"
    with fabrica() as bd:
        assert (
            bd.scalar(select(Apartaestudio.id).where(Apartaestudio.codigo == f"{PREFIJO}P10"))
            is None
        )


def test_intercambio_simultaneo_de_propietarios_no_produce_bloqueo_mutuo(fabrica, monkeypatch):
    p1 = nuevo_propietario(fabrica, "880000003")
    p2 = nuevo_propietario(fabrica, "880000004")
    a = nuevo_apartaestudio(fabrica, f"{PREFIJO}A", p1)
    b = nuevo_apartaestudio(fabrica, f"{PREFIJO}B", p2)
    # Cada petición tiene bloqueado su apartaestudio antes de pedir los dos propietarios.
    salida = threading.Barrier(2)
    original = repositorio.bloquear_propietarios

    def bloquear_a_la_vez(*args, **kwargs):
        salida.wait(timeout=10)
        return original(*args, **kwargs)

    monkeypatch.setattr(repositorio, "bloquear_propietarios", bloquear_a_la_vez)

    def pasar(apto_id, destino):
        def tarea():
            with fabrica() as bd:
                apartaestudios.editar(
                    bd,
                    apto_id,
                    ApartaestudioEditar(propietario_id=destino),
                    actor_id=None,
                    ip=None,
                    hoy=HOY,
                )
                bd.commit()

        return tarea

    assert en_paralelo(pasar(a, p2), pasar(b, p1)) == ["ok", "ok"]
    with fabrica() as bd:
        assert bd.get(Apartaestudio, a).propietario_id == p2
        assert bd.get(Apartaestudio, b).propietario_id == p1
