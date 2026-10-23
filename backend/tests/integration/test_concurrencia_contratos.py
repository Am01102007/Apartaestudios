"""Contratos con transacciones reales en conexiones separadas (C-05, C-06).

Confirman datos de verdad. Cada ejecución usa un propietario, apartaestudios y documentos
nuevos (sufijo aleatorio), y al final los apartaestudios quedan inactivos.
"""

import secrets
import threading
import time
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import delete, func, select, text, update

from app.core.errores import ReglaDeNegocio
from app.db.sesion import crear_fabrica
from app.modulos.bloqueos import repositorio as repositorio_bloqueos
from app.modulos.bloqueos import servicio as bloqueos
from app.modulos.bloqueos.esquemas import BloqueoCrear
from app.modulos.contratos import repositorio, servicio
from app.modulos.contratos.esquemas import ContratoCrear, RenovacionCrear
from app.modulos.contratos.modelos import Contrato, Prorroga
from app.modulos.inmuebles import apartaestudios, propietarios
from app.modulos.inmuebles.esquemas import ApartaestudioCrear, PropietarioCrear
from app.modulos.inmuebles.modelos import Apartaestudio, Propietario
from app.modulos.residentes import servicio as residentes
from app.modulos.residentes.esquemas import ResidenteCrear
from app.modulos.usuarios import servicio as usuarios
from app.modulos.usuarios.esquemas import UsuarioCrear
from app.modulos.usuarios.modelos import Rol, Usuario
from tests.integration.ayudas import en_paralelo

pytestmark = pytest.mark.integracion
HOY = date(2026, 10, 17)
AHORA = datetime(2026, 10, 17, 15, 0, tzinfo=UTC)
PREFIJO = "CCT-"


@pytest.fixture
def fabrica(motor_pruebas):
    fabrica = crear_fabrica(motor_pruebas)
    yield fabrica
    # Los contratos se retiran (con el dueño de las tablas; la API no puede borrarlos) para
    # que no aparezcan en las listas de otras pruebas. Lo demás queda inactivo.
    with motor_pruebas.begin() as conexion:
        de_prueba = (
            select(Contrato.id)
            .join(Contrato.apartaestudio)
            .where(Apartaestudio.codigo.startswith(PREFIJO))
        )
        conexion.execute(delete(Prorroga).where(Prorroga.contrato_id.in_(de_prueba)))
        conexion.execute(
            delete(Contrato).where(
                Contrato.id.in_(de_prueba), Contrato.contrato_anterior_id.is_not(None)
            )
        )
        conexion.execute(delete(Contrato).where(Contrato.id.in_(de_prueba)))
        conexion.execute(
            update(Apartaestudio)
            .where(Apartaestudio.codigo.startswith(PREFIJO))
            .values(activo=False)
        )
        conexion.execute(
            update(Propietario).where(Propietario.nombre.startswith(PREFIJO)).values(activo=False)
        )
        conexion.execute(
            update(Usuario).where(Usuario.nombre_usuario == "conc_contratos").values(activo=False)
        )


@pytest.fixture
def admin_id(fabrica):
    with fabrica() as bd:
        existente = bd.scalar(select(Usuario).where(Usuario.nombre_usuario == "conc_contratos"))
        if existente:
            existente.activo = True
            bd.commit()
            return existente.id
        admin = usuarios.crear(
            bd,
            UsuarioCrear(
                nombre_usuario="conc_contratos",
                nombre="Zz contratos",
                rol=Rol.ADMINISTRADOR,
                contrasena_temporal="contrasena-segura-1",
            ),
            actor_id=None,
            ip=None,
        )
        bd.commit()
        return admin.id


def _documento() -> str:
    return f"98{secrets.randbelow(10**8):08d}"


@pytest.fixture
def escenario(fabrica, admin_id):
    """Un apartaestudio y dos residentes nuevos."""
    with fabrica() as bd:
        propietario = propietarios.crear(
            bd,
            PropietarioCrear(
                nombre=f"{PREFIJO}Dueño", tipo_documento="CC", numero_documento=_documento()
            ),
            actor_id=admin_id,
            ip=None,
        )
        apartaestudio = apartaestudios.crear(
            bd,
            ApartaestudioCrear(
                codigo=f"{PREFIJO}{secrets.token_hex(3).upper()}",
                propietario_id=propietario.id,
                direccion="Calle 1",
            ),
            actor_id=admin_id,
            ip=None,
            hoy=HOY,
        )
        personas = [
            residentes.crear(
                bd,
                ResidenteCrear(
                    nombre=f"{PREFIJO}Persona {i}",
                    tipo_documento="CC",
                    numero_documento=_documento(),
                    telefono="3000000000",
                ),
                actor_id=admin_id,
                ip=None,
            )
            for i in range(2)
        ]
        bd.commit()
        return apartaestudio.id, [p.id for p in personas], [p.numero_documento for p in personas]


def _crear(fabrica, admin_id, apartaestudio_id, residente_id, inicio="2026-10-20"):
    def tarea():
        with fabrica() as bd:
            servicio.crear(
                bd,
                ContratoCrear(
                    apartaestudio_id=apartaestudio_id,
                    residente_id=residente_id,
                    fecha_inicio=inicio,
                    fecha_terminacion="2027-10-19",
                    canon_inicial=850000,
                    porcentaje_incremento=5,
                ),
                actor_id=admin_id,
                ip=None,
                hoy=HOY,
            )
            bd.commit()

    return tarea


def _contratos(fabrica, apartaestudio_id) -> int:
    with fabrica() as bd:
        return bd.scalar(
            select(func.count())
            .select_from(Contrato)
            .where(Contrato.apartaestudio_id == apartaestudio_id)
        )


def _un_rechazo(resultados, codigo):
    assert resultados.count("ok") == 1, resultados
    rechazo = next(r for r in resultados if r != "ok")
    assert isinstance(rechazo, ReglaDeNegocio) and rechazo.codigo == codigo, rechazo


def test_c06_dos_contratos_simultaneos_sobre_el_mismo_apartaestudio(
    fabrica, admin_id, escenario, monkeypatch
):
    apartaestudio_id, (uno, otro), _ = escenario
    # Cada petición se detiene después de su verificación: si el apartaestudio no las
    # ordenara, las dos verían que está libre.
    original = repositorio.apartaestudio_reservado

    def despacio(*args, **kwargs):
        resultado = original(*args, **kwargs)
        time.sleep(0.3)
        return resultado

    monkeypatch.setattr(repositorio, "apartaestudio_reservado", despacio)
    resultados = en_paralelo(
        _crear(fabrica, admin_id, apartaestudio_id, uno),
        _crear(fabrica, admin_id, apartaestudio_id, otro),
    )
    _un_rechazo(resultados, "apartaestudio_reservado")
    assert _contratos(fabrica, apartaestudio_id) == 1


def test_c06_la_restriccion_de_exclusion_respalda_la_regla(
    fabrica, admin_id, escenario, monkeypatch
):
    # Sin el bloqueo del apartaestudio, las dos pasan la verificación a la vez y solo la
    # restricción de exclusión de la base de datos puede detener a la segunda.
    apartaestudio_id, (uno, otro), _ = escenario
    from app.modulos.inmuebles import repositorio as inmuebles

    original_obtener = inmuebles.obtener_apartaestudio
    monkeypatch.setattr(
        inmuebles,
        "obtener_apartaestudio",
        lambda sesion, id_, *, bloquear=False: original_obtener(sesion, id_),
    )
    salida = threading.Barrier(2)
    original = repositorio.apartaestudio_reservado

    def a_la_vez(*args, **kwargs):
        resultado = original(*args, **kwargs)
        salida.wait(timeout=10)
        return resultado

    monkeypatch.setattr(repositorio, "apartaestudio_reservado", a_la_vez)
    resultados = en_paralelo(
        _crear(fabrica, admin_id, apartaestudio_id, uno, inicio="2026-10-20"),
        _crear(fabrica, admin_id, apartaestudio_id, otro, inicio="2026-11-20"),
    )
    _un_rechazo(resultados, "apartaestudio_reservado")
    assert _contratos(fabrica, apartaestudio_id) == 1


def test_ca03_contrato_y_bloqueo_simultaneos_de_la_misma_persona(
    fabrica, admin_id, escenario, monkeypatch
):
    """Si alguien está bloqueando a la persona, el contrato espera y luego ve el bloqueo."""
    apartaestudio_id, (uno, _), (documento, _) = escenario
    bloqueando = threading.Event()
    continuar = threading.Event()
    contrato_terminado = threading.Event()
    original = repositorio_bloqueos.activo_de

    def activo_de_despacio(*args, **kwargs):
        resultado = original(*args, **kwargs)
        if threading.current_thread().name == "bloquear":
            bloqueando.set()  # ya tiene el bloqueo del documento
            continuar.wait(timeout=10)
        return resultado

    monkeypatch.setattr(repositorio_bloqueos, "activo_de", activo_de_despacio)

    def bloquear():
        threading.current_thread().name = "bloquear"
        with fabrica() as bd:
            bloqueos.bloquear(
                bd,
                BloqueoCrear(
                    tipo_documento="CC",
                    numero_documento=documento,
                    nombre=f"{PREFIJO}Persona",
                    motivo="Prueba",
                ),
                actor_id=admin_id,
                ip=None,
                ahora=AHORA,
            )
            bd.commit()

    crear = _crear(fabrica, admin_id, apartaestudio_id, uno)

    def contratar():
        bloqueando.wait(timeout=10)
        try:
            crear()
        finally:
            contrato_terminado.set()

    def soltar():
        bloqueando.wait(timeout=10)
        time.sleep(0.5)
        assert not contrato_terminado.is_set(), "el contrato no esperó al bloqueo"
        continuar.set()

    resultados = en_paralelo(bloquear, contratar, soltar)
    assert resultados[0] == "ok" and resultados[2] == "ok", resultados
    assert isinstance(resultados[1], ReglaDeNegocio), resultados
    assert resultados[1].codigo == "persona_bloqueada"
    assert _contratos(fabrica, apartaestudio_id) == 0


def test_renovacion_y_contrato_nuevo_simultaneos_sobre_el_mismo_apartaestudio(
    fabrica, admin_id, escenario
):
    apartaestudio_id, (uno, otro), _ = escenario
    _crear(fabrica, admin_id, apartaestudio_id, uno, inicio="2026-10-17")()
    with fabrica() as bd:
        contrato_id = bd.scalar(
            select(Contrato.id).where(Contrato.apartaestudio_id == apartaestudio_id)
        )

    def renovar():
        with fabrica() as bd:
            servicio.renovar(
                bd,
                contrato_id,
                RenovacionCrear(fecha_terminacion="2028-10-16", porcentaje_incremento=4),
                actor_id=admin_id,
                ip=None,
                hoy=HOY,
            )
            bd.commit()

    resultados = en_paralelo(renovar, _crear(fabrica, admin_id, apartaestudio_id, otro))
    assert resultados[0] == "ok", resultados
    assert isinstance(resultados[1], ReglaDeNegocio), resultados
    assert resultados[1].codigo == "apartaestudio_reservado"
    assert _contratos(fabrica, apartaestudio_id) == 2


def test_la_exclusion_existe_en_la_base_de_datos(fabrica):
    with fabrica() as bd:
        definicion = bd.scalar(
            text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'ex_contratos_reserva'"
            )
        )
    assert "EXCLUDE USING gist" in definicion and "anulado_en IS NULL" in definicion
