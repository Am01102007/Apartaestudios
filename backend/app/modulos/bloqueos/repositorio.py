from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app.core.documentos import TipoDocumento, normalizar_documento
from app.db.consultas import patron_busqueda
from app.modulos.bloqueos.modelos import Bloqueo, EstadoBloqueo


def bloquear_documento(sesion: Session, tipo: TipoDocumento, numero: str) -> None:
    """Bloqueo de PostgreSQL sobre el documento hasta el fin de la transacción.

    Bloquear a una persona y firmarle un contrato toman este mismo bloqueo, así que nunca se
    cruzan: el segundo espera y ve lo que hizo el primero (CA-03).
    """
    sesion.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:clave, 0))"),
        {"clave": f"documento:{tipo}:{numero}"},
    )


def activo_de(sesion: Session, tipo: TipoDocumento, numero: str) -> Bloqueo | None:
    return sesion.scalar(
        select(Bloqueo).where(
            Bloqueo.tipo_documento == tipo,
            Bloqueo.numero_documento == numero,
            Bloqueo.levantado_en.is_(None),
        )
    )


def obtener(sesion: Session, bloqueo_id: int, *, bloquear: bool = False) -> Bloqueo | None:
    consulta = select(Bloqueo).where(Bloqueo.id == bloqueo_id)
    if bloquear:
        consulta = consulta.with_for_update(of=Bloqueo).execution_options(populate_existing=True)
    return sesion.scalar(consulta)


def listar(sesion: Session, *, estado: EstadoBloqueo, texto: str | None) -> list[Bloqueo]:
    consulta = select(Bloqueo).order_by(Bloqueo.bloqueado_en.desc(), Bloqueo.id.desc())
    if estado == EstadoBloqueo.ACTIVOS:
        consulta = consulta.where(Bloqueo.levantado_en.is_(None))
    elif estado == EstadoBloqueo.LEVANTADOS:
        consulta = consulta.where(Bloqueo.levantado_en.is_not(None))
    if texto:
        consulta = consulta.where(
            or_(
                Bloqueo.nombre.ilike(patron_busqueda(texto), escape="\\"),
                Bloqueo.numero_documento.ilike(
                    patron_busqueda(normalizar_documento(texto)), escape="\\"
                ),
            )
        )
    return list(sesion.scalars(consulta))
