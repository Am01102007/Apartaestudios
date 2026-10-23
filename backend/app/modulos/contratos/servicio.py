"""Contratos y su ciclo de vida (RF-08 a RF-10, RN-04 a RN-12).

Las funciones validan, modifican y auditan, pero no confirman: lo hace el endpoint.

Orden de bloqueos, siempre el mismo: el apartaestudio, el residente, el contrato (con una
renovación, primero el anterior y después el nuevo) y, al final, el documento del residente,
que es el mismo bloqueo que toma `POST /bloqueos` (CA-03). Si aun así dos peticiones cruzan
reservas, la restricción de exclusión de la base de datos lo impide.
"""

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import DatosInvalidos, NoEncontrado, ReglaDeNegocio
from app.modulos.auditoria import servicio as auditoria
from app.modulos.auditoria.modelos import RegistroAuditoria
from app.modulos.bloqueos import servicio as bloqueos
from app.modulos.contratos import estados, repositorio
from app.modulos.contratos.esquemas import (
    ContratoCrear,
    ContratoEditar,
    RenovacionCrear,
    TerminacionCrear,
)
from app.modulos.contratos.estados import EN_CURSO, EstadoContrato
from app.modulos.contratos.modelos import Contrato, Prorroga
from app.modulos.inmuebles import repositorio as inmuebles
from app.modulos.inmuebles.comun import cambios_de, instantanea
from app.modulos.residentes import repositorio as residentes

ENTIDAD = "contrato"
CAMPOS_AUDITADOS = (
    "apartaestudio_id",
    "residente_id",
    "fecha_inicio",
    "fecha_terminacion",
    "canon_inicial",
    "porcentaje_incremento",
    "notas",
    "contrato_anterior_id",
)
_UN_DIA = timedelta(days=1)


# --- Errores --------------------------------------------------------------------------------


def _reservado() -> ReglaDeNegocio:
    return ReglaDeNegocio(
        "El apartaestudio tiene otro contrato por iniciar, vigente, vencido o en terminación.",
        codigo="apartaestudio_reservado",
    )


def _no_permite(estado: EstadoContrato, operacion: str) -> ReglaDeNegocio:
    return ReglaDeNegocio(
        f"Un contrato en estado «{estado.value}» no se puede {operacion}.",
        codigo="estado_no_permite",
    )


def _invalido(campo: str, mensaje: str) -> DatosInvalidos:
    return DatosInvalidos(f"{mensaje}.", [{"campo": campo, "mensaje": mensaje}])


# --- Cálculos para la salida ----------------------------------------------------------------


def estado_de(contrato: Contrato, hoy: date) -> EstadoContrato:
    return estados.estado(
        hoy,
        fecha_inicio=contrato.fecha_inicio,
        fecha_terminacion=contrato.fecha_terminacion,
        fecha_entrega=contrato.fecha_entrega,
        fin_reserva=contrato.fin_reserva,
        anulado=contrato.anulado_en is not None,
    )


def _completar(contrato: Contrato, estado: str, siguiente_id: int | None) -> Contrato:
    """Añade los datos calculados que devuelve el endpoint."""
    contrato.estado = EstadoContrato(estado)
    # Hasta el módulo de incrementos, el canon vigente es el inicial.
    contrato.canon_vigente = contrato.canon_inicial
    contrato.contrato_siguiente_id = siguiente_id
    return contrato


def _detalle(sesion: Session, contrato: Contrato, hoy: date) -> Contrato:
    sesion.flush()
    fila = repositorio.calculados(sesion, contrato.id, hoy)
    _completar(contrato, fila.estado, fila.siguiente_id)

    activo = contrato.estado in estados.OCUPAN or contrato.estado == EstadoContrato.POR_INICIAR
    corte = estados.proximo_corte(contrato.fecha_inicio, hoy) if activo else None
    aniversario = estados.proximo_aniversario(contrato.fecha_inicio, hoy) if activo else None
    if contrato.fin_reserva is not None:
        # Después de la entrega o de la renovación ya no hay cortes ni aniversarios.
        corte = corte if corte and corte <= contrato.fin_reserva else None
        aniversario = aniversario if aniversario and aniversario <= contrato.fin_reserva else None
    contrato.dia_corte = contrato.fecha_inicio.day
    contrato.proximo_corte = corte
    contrato.proximo_aniversario = aniversario
    contrato.prorrogas = repositorio.prorrogas(sesion, contrato.id)
    return contrato


def tiene_cobros(sesion: Session, contrato: Contrato) -> bool:
    """RN-09. El módulo de cobros la conecta; hasta entonces ningún contrato tiene cobros."""
    del sesion, contrato
    return False


# --- Consultas ------------------------------------------------------------------------------


def _obtener(sesion: Session, contrato_id: int, *, bloquear: bool = False) -> Contrato:
    contrato = repositorio.obtener(sesion, contrato_id, bloquear=bloquear)
    if contrato is None:
        raise NoEncontrado("El contrato no existe.")
    return contrato


def obtener(sesion: Session, contrato_id: int, *, hoy: date) -> Contrato:
    return _detalle(sesion, _obtener(sesion, contrato_id), hoy)


def listar(sesion: Session, *, hoy: date, **filtros: Any) -> list[Contrato]:
    return [
        _completar(fila.Contrato, fila.estado, fila.siguiente_id)
        for fila in repositorio.listar(sesion, hoy=hoy, **filtros)
    ]


def de_apartaestudio(sesion: Session, apartaestudio_id: int, *, hoy: date) -> list[Contrato]:
    if inmuebles.obtener_apartaestudio(sesion, apartaestudio_id) is None:
        raise NoEncontrado("El apartaestudio no existe.")
    return listar(sesion, hoy=hoy, apartaestudio_id=apartaestudio_id)


def de_residente(sesion: Session, residente_id: int, *, hoy: date) -> list[Contrato]:
    if residentes.obtener(sesion, residente_id) is None:
        raise NoEncontrado("El residente no existe.")
    return listar(sesion, hoy=hoy, residente_id=residente_id)


def actuales_de_residente(sesion: Session, residente_id: int, *, hoy: date) -> list[Contrato]:
    """Contratos por iniciar, vigentes, vencidos o en terminación del residente."""
    return [
        contrato
        for contrato in listar(sesion, hoy=hoy, residente_id=residente_id)
        if contrato.estado in estados.OCUPAN or contrato.estado == EstadoContrato.POR_INICIAR
    ]


def historial(sesion: Session, contrato_id: int) -> list[RegistroAuditoria]:
    """RF-10: los cambios del contrato con autor y fecha, del más antiguo al más reciente."""
    _obtener(sesion, contrato_id)
    return auditoria.de_entidad(sesion, ENTIDAD, contrato_id)


# --- Validaciones comunes -------------------------------------------------------------------


def _exigir_inicio_no_pasado(fecha_inicio: date, hoy: date) -> None:
    # D-1: no se registran contratos con inicio pasado.
    if fecha_inicio < hoy:
        raise _invalido("fecha_inicio", "La fecha de inicio no puede ser anterior a hoy")


def _bloquear_partes(sesion: Session, apartaestudio_id: int, residente_id: int):
    """Bloquea el apartaestudio y el residente, en ese orden, y los valida (RC-05)."""
    apartaestudio = inmuebles.obtener_apartaestudio(sesion, apartaestudio_id, bloquear=True)
    if apartaestudio is None:
        raise NoEncontrado("El apartaestudio no existe.")
    if not apartaestudio.activo:
        raise ReglaDeNegocio("El apartaestudio está inactivo.", codigo="apartaestudio_inactivo")
    residente = residentes.obtener(sesion, residente_id, bloquear=True)
    if residente is None:
        raise NoEncontrado("El residente no existe.")
    return apartaestudio, residente


def _guardar_reserva(sesion: Session) -> None:
    """Si dos contratos cruzan sus reservas, la restricción de exclusión lo detiene y se
    informa como regla de negocio; la petición termina sin confirmar."""
    try:
        sesion.flush()
    except IntegrityError as exc:
        raise _reservado() from exc


def _auditar(
    sesion: Session,
    accion: str,
    contrato: Contrato,
    *,
    actor_id: int,
    ip: str | None,
    antes: dict | None = None,
    despues: dict | None = None,
) -> None:
    auditoria.registrar(
        sesion,
        accion=f"contrato.{accion}",
        entidad=ENTIDAD,
        entidad_id=contrato.id,
        usuario_id=actor_id,
        antes=antes,
        despues=despues,
        ip=ip,
    )


# --- Operaciones ----------------------------------------------------------------------------


def crear(
    sesion: Session, datos: ContratoCrear, *, actor_id: int, ip: str | None, hoy: date
) -> Contrato:
    _exigir_inicio_no_pasado(datos.fecha_inicio, hoy)
    _, residente = _bloquear_partes(sesion, datos.apartaestudio_id, datos.residente_id)
    bloqueos.exigir_sin_bloqueo(sesion, residente.tipo_documento, residente.numero_documento)
    if repositorio.apartaestudio_reservado(sesion, datos.apartaestudio_id, hoy):
        raise _reservado()

    contrato = Contrato(**datos.model_dump(), creado_por_id=actor_id)
    sesion.add(contrato)
    _guardar_reserva(sesion)
    _auditar(
        sesion,
        "crear",
        contrato,
        actor_id=actor_id,
        ip=ip,
        despues=instantanea(contrato, CAMPOS_AUDITADOS),
    )
    return _detalle(sesion, contrato, hoy)


def editar(
    sesion: Session,
    contrato_id: int,
    datos: ContratoEditar,
    *,
    actor_id: int,
    ip: str | None,
    hoy: date,
) -> Contrato:
    contrato = _obtener(sesion, contrato_id, bloquear=True)
    estado = estado_de(contrato, hoy)
    if estado not in EN_CURSO | {EstadoContrato.POR_INICIAR}:
        raise _no_permite(estado, "editar")
    if repositorio.renovacion_de(sesion, contrato.id) is not None:
        raise ReglaDeNegocio(
            "El contrato ya tiene una renovación registrada.", codigo="ya_renovado"
        )
    if tiene_cobros(sesion, contrato):
        raise ReglaDeNegocio(
            "El contrato ya tiene cobros: cambia solo por incremento, prórroga, renovación o "
            "terminación.",
            codigo="tiene_cobros",
        )
    cambios = cambios_de(contrato, datos.model_dump(exclude_unset=True))
    if not cambios:
        return _detalle(sesion, contrato, hoy)

    if "fecha_inicio" in cambios:
        if estado != EstadoContrato.POR_INICIAR or contrato.contrato_anterior_id is not None:
            raise _invalido(
                "fecha_inicio",
                "La fecha de inicio solo se cambia en contratos por iniciar que no son "
                "renovaciones",
            )
        _exigir_inicio_no_pasado(cambios["fecha_inicio"], hoy)
    inicio = cambios.get("fecha_inicio", contrato.fecha_inicio)
    if cambios.get("fecha_terminacion", contrato.fecha_terminacion) <= inicio:
        raise _invalido(
            "fecha_terminacion", "La fecha de terminación debe ser posterior a la de inicio"
        )

    antes = instantanea(contrato, tuple(cambios))
    for campo, valor in cambios.items():
        setattr(contrato, campo, valor)
    _guardar_reserva(sesion)
    _auditar(
        sesion,
        "editar",
        contrato,
        actor_id=actor_id,
        ip=ip,
        antes=antes,
        despues=instantanea(contrato, tuple(cambios)),
    )
    return _detalle(sesion, contrato, hoy)


def _en_curso_sin_renovacion(
    sesion: Session, contrato: Contrato, hoy: date, operacion: str
) -> EstadoContrato:
    estado = estado_de(contrato, hoy)
    if estado not in EN_CURSO:
        raise _no_permite(estado, operacion)
    if repositorio.renovacion_de(sesion, contrato.id) is not None:
        raise ReglaDeNegocio(
            "El contrato ya tiene una renovación registrada.", codigo="ya_renovado"
        )
    return estado


def prorrogar(
    sesion: Session,
    contrato_id: int,
    fecha_terminacion: date,
    *,
    actor_id: int,
    ip: str | None,
    ahora: datetime,
    hoy: date,
) -> Contrato:
    """RC-08: extiende el mismo contrato. RN-07 no impide prórrogas a personas bloqueadas."""
    contrato = _obtener(sesion, contrato_id, bloquear=True)
    _en_curso_sin_renovacion(sesion, contrato, hoy, "prorrogar")
    if fecha_terminacion <= contrato.fecha_terminacion:
        raise _invalido("fecha_terminacion", "La nueva terminación debe ser posterior a la actual")
    if fecha_terminacion < hoy:
        raise _invalido("fecha_terminacion", "La nueva terminación no puede ser anterior a hoy")

    anterior = contrato.fecha_terminacion
    contrato.fecha_terminacion = fecha_terminacion
    sesion.add(
        Prorroga(
            contrato_id=contrato.id,
            terminacion_anterior=anterior,
            terminacion_nueva=fecha_terminacion,
            registrada_por_id=actor_id,
            registrada_en=ahora,
        )
    )
    _auditar(
        sesion,
        "prorrogar",
        contrato,
        actor_id=actor_id,
        ip=ip,
        antes={"fecha_terminacion": anterior},
        despues={"fecha_terminacion": fecha_terminacion},
    )
    return _detalle(sesion, contrato, hoy)


def renovar(
    sesion: Session,
    contrato_id: int,
    datos: RenovacionCrear,
    *,
    actor_id: int,
    ip: str | None,
    hoy: date,
) -> Contrato:
    """RC-09 y D-2: cierra el contrato y crea el nuevo, enlazado, sin hueco ni traslape."""
    sin_bloquear = _obtener(sesion, contrato_id)
    _, residente = _bloquear_partes(
        sesion, sin_bloquear.apartaestudio_id, sin_bloquear.residente_id
    )
    anterior = _obtener(sesion, contrato_id, bloquear=True)
    _en_curso_sin_renovacion(sesion, anterior, hoy, "renovar")
    bloqueos.exigir_sin_bloqueo(sesion, residente.tipo_documento, residente.numero_documento)

    inicio = estados.inicio_renovacion(anterior.fecha_inicio, anterior.fecha_terminacion, hoy)
    if datos.fecha_terminacion <= inicio:
        raise _invalido(
            "fecha_terminacion",
            f"La terminación debe ser posterior al inicio de la renovación ({inicio})",
        )

    anterior.fin_reserva = inicio - _UN_DIA
    sesion.flush()
    nuevo = Contrato(
        apartaestudio_id=anterior.apartaestudio_id,
        residente_id=anterior.residente_id,
        fecha_inicio=inicio,
        fecha_terminacion=datos.fecha_terminacion,
        # Hasta el módulo de incrementos, el canon vigente es el inicial.
        canon_inicial=datos.canon_inicial or anterior.canon_inicial,
        porcentaje_incremento=datos.porcentaje_incremento,
        notas=datos.notas,
        contrato_anterior_id=anterior.id,
        creado_por_id=actor_id,
    )
    sesion.add(nuevo)
    _guardar_reserva(sesion)

    _auditar(
        sesion,
        "renovar",
        anterior,
        actor_id=actor_id,
        ip=ip,
        antes={"fin_reserva": None},
        despues={"fin_reserva": anterior.fin_reserva, "contrato_nuevo_id": nuevo.id},
    )
    _auditar(
        sesion,
        "crear",
        nuevo,
        actor_id=actor_id,
        ip=ip,
        despues=instantanea(nuevo, CAMPOS_AUDITADOS),
    )
    return _detalle(sesion, nuevo, hoy)


def terminar(
    sesion: Session,
    contrato_id: int,
    datos: TerminacionCrear,
    *,
    actor_id: int,
    ip: str | None,
    hoy: date,
) -> Contrato:
    """RC-10 y D-3: registra aviso, entrega y motivo; mientras la entrega no haya pasado, se
    puede registrar de nuevo para corregirla."""
    contrato = _obtener(sesion, contrato_id, bloquear=True)
    estado = estado_de(contrato, hoy)
    if estado != EstadoContrato.EN_TERMINACION:
        _en_curso_sin_renovacion(sesion, contrato, hoy, "terminar")
    if datos.fecha_aviso > hoy:
        raise _invalido("fecha_aviso", "La fecha de aviso no puede ser futura")
    if datos.fecha_entrega < contrato.fecha_inicio:
        raise _invalido("fecha_entrega", "La entrega no puede ser anterior al inicio")

    campos = ("fecha_aviso", "fecha_entrega", "motivo_terminacion")
    antes = instantanea(contrato, campos)
    contrato.fecha_aviso = datos.fecha_aviso
    contrato.fecha_entrega = datos.fecha_entrega
    contrato.motivo_terminacion = datos.motivo
    contrato.terminacion_registrada_por_id = actor_id
    contrato.fin_reserva = datos.fecha_entrega
    _guardar_reserva(sesion)
    _auditar(
        sesion,
        "corregir_terminacion" if estado == EstadoContrato.EN_TERMINACION else "terminar",
        contrato,
        actor_id=actor_id,
        ip=ip,
        antes=antes,
        despues=instantanea(contrato, campos),
    )
    return _detalle(sesion, contrato, hoy)


def anular(
    sesion: Session,
    contrato_id: int,
    motivo: str,
    *,
    actor_id: int,
    ip: str | None,
    ahora: datetime,
    hoy: date,
) -> Contrato:
    """RC-11: solo contratos por iniciar. Si era una renovación, el anterior vuelve a quedar
    sin fin de reserva."""
    contrato = _obtener(sesion, contrato_id)
    anterior = None
    if contrato.contrato_anterior_id is not None:
        # Mismo orden de bloqueos que renovar: el anterior antes que el nuevo.
        anterior = _obtener(sesion, contrato.contrato_anterior_id, bloquear=True)
    contrato = _obtener(sesion, contrato_id, bloquear=True)
    estado = estado_de(contrato, hoy)
    if estado != EstadoContrato.POR_INICIAR:
        raise _no_permite(estado, "anular")

    contrato.anulado_en = ahora
    contrato.anulado_por_id = actor_id
    contrato.motivo_anulacion = motivo
    _auditar(sesion, "anular", contrato, actor_id=actor_id, ip=ip, despues={"motivo": motivo})
    if anterior is not None:
        sesion.flush()
        anterior.fin_reserva = None
        _auditar(
            sesion,
            "anular_renovacion",
            anterior,
            actor_id=actor_id,
            ip=ip,
            antes={"contrato_nuevo_id": contrato.id},
            despues={"fin_reserva": None},
        )
    sesion.flush()
    return _detalle(sesion, contrato, hoy)
