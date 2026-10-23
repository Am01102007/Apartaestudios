"""Bloquear, levantar y consultar bloqueos (RF-07, RN-07).

Las funciones validan, modifican y auditan, pero no confirman: lo hace el endpoint.
`exigir_sin_bloqueo` es lo que usará el módulo de contratos (CA-03).
"""

from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.documentos import TipoDocumento
from app.core.errores import NoEncontrado, ReglaDeNegocio
from app.modulos.auditoria import servicio as auditoria
from app.modulos.bloqueos import repositorio
from app.modulos.bloqueos.esquemas import BloqueoCrear, BloqueoSalida
from app.modulos.bloqueos.modelos import Bloqueo, EstadoBloqueo

ENTIDAD = "bloqueo"


def _ya_bloqueado(tipo: TipoDocumento, numero: str) -> ReglaDeNegocio:
    return ReglaDeNegocio(
        f"El documento {tipo} {numero} ya tiene un bloqueo activo.", codigo="ya_bloqueado"
    )


def salida(bloqueo: Bloqueo, *, ve_motivos: bool) -> BloqueoSalida:
    """D-3: el empleado ve que existe el bloqueo y desde cuándo, pero no los motivos."""
    datos = BloqueoSalida.model_validate(bloqueo)
    if ve_motivos:
        return datos
    return datos.model_copy(update={"motivo": None, "motivo_levantamiento": None})


def bloqueo_activo(sesion: Session, tipo: TipoDocumento, numero: str) -> Bloqueo | None:
    return repositorio.activo_de(sesion, tipo, numero)


def exigir_sin_bloqueo(sesion: Session, tipo: TipoDocumento, numero: str) -> None:
    """RN-07: falla si el documento tiene un bloqueo activo. Toma el bloqueo del documento
    hasta el fin de la transacción, para que nadie lo bloquee mientras se firma el contrato."""
    repositorio.bloquear_documento(sesion, tipo, numero)
    if repositorio.activo_de(sesion, tipo, numero) is not None:
        raise ReglaDeNegocio(
            "La persona tiene un bloqueo activo y no puede firmar contratos nuevos.",
            codigo="persona_bloqueada",
        )


def listar(
    sesion: Session, *, estado: EstadoBloqueo = EstadoBloqueo.ACTIVOS, texto: str | None = None
) -> list[Bloqueo]:
    return repositorio.listar(sesion, estado=estado, texto=texto)


def bloquear(
    sesion: Session, datos: BloqueoCrear, *, actor_id: int, ip: str | None, ahora: datetime
) -> Bloqueo:
    tipo, numero = datos.tipo_documento, datos.numero_documento
    repositorio.bloquear_documento(sesion, tipo, numero)
    if repositorio.activo_de(sesion, tipo, numero) is not None:
        raise _ya_bloqueado(tipo, numero)

    bloqueo = Bloqueo(
        tipo_documento=tipo,
        numero_documento=numero,
        nombre=datos.nombre,
        motivo=datos.motivo,
        bloqueado_en=ahora,
        bloqueado_por_id=actor_id,
    )
    sesion.add(bloqueo)
    try:
        # Respaldo del bloqueo del documento: el índice único parcial (RR-04).
        sesion.flush()
    except IntegrityError as exc:
        raise _ya_bloqueado(tipo, numero) from exc
    sesion.refresh(bloqueo, ["bloqueado_por"])

    auditoria.registrar(
        sesion,
        accion="bloqueo.crear",
        entidad=ENTIDAD,
        entidad_id=bloqueo.id,
        usuario_id=actor_id,
        despues={
            "tipo_documento": tipo,
            "numero_documento": numero,
            "nombre": datos.nombre,
            "motivo": datos.motivo,
        },
        ip=ip,
    )
    return bloqueo


def levantar(
    sesion: Session,
    bloqueo_id: int,
    motivo: str,
    *,
    actor_id: int,
    ip: str | None,
    ahora: datetime,
) -> Bloqueo:
    bloqueo = repositorio.obtener(sesion, bloqueo_id, bloquear=True)
    if bloqueo is None:
        raise NoEncontrado("El bloqueo no existe.")
    if not bloqueo.activo:
        raise ReglaDeNegocio("Este bloqueo ya fue levantado.", codigo="ya_levantado")

    bloqueo.levantado_en = ahora
    bloqueo.levantado_por_id = actor_id
    bloqueo.motivo_levantamiento = motivo
    sesion.flush()
    sesion.refresh(bloqueo, ["levantado_por"])

    auditoria.registrar(
        sesion,
        accion="bloqueo.levantar",
        entidad=ENTIDAD,
        entidad_id=bloqueo.id,
        usuario_id=actor_id,
        antes={"activo": True},
        despues={"activo": False, "motivo": motivo},
        ip=ip,
    )
    return bloqueo
