from datetime import date

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import Session

from app.core.documentos import TipoDocumento
from app.db.consultas import patron_busqueda
from app.modulos.contratos import consultas as contratos
from app.modulos.inmuebles.modelos import Apartaestudio, Propietario


def _bloqueando(consulta, bloquear: bool):
    # populate_existing: tras esperar el bloqueo, se leen los valores ya confirmados.
    if bloquear:
        return consulta.with_for_update().execution_options(populate_existing=True)
    return consulta


# --- Propietarios ---------------------------------------------------------------------------


def obtener_propietario(
    sesion: Session, propietario_id: int, *, bloquear: bool = False
) -> Propietario | None:
    consulta = select(Propietario).where(Propietario.id == propietario_id)
    return sesion.scalar(_bloqueando(consulta, bloquear))


def bloquear_propietarios(sesion: Session, ids: set[int]) -> dict[int, Propietario]:
    """Bloquea varios propietarios en orden de id, para no esperarse mutuamente con otra
    petición que bloquee los mismos."""
    consulta = select(Propietario).where(Propietario.id.in_(ids)).order_by(Propietario.id)
    return {p.id: p for p in sesion.scalars(_bloqueando(consulta, True))}


def existe_documento(
    sesion: Session, tipo: TipoDocumento, numero: str, excepto_id: int | None = None
) -> bool:
    consulta = select(Propietario.id).where(
        Propietario.tipo_documento == tipo, Propietario.numero_documento == numero
    )
    if excepto_id is not None:
        consulta = consulta.where(Propietario.id != excepto_id)
    return sesion.scalar(consulta) is not None


def listar_propietarios(
    sesion: Session, *, activo: bool | None, texto: str | None
) -> list[Propietario]:
    consulta = select(Propietario).order_by(Propietario.nombre, Propietario.id)
    if activo is not None:
        consulta = consulta.where(Propietario.activo == activo)
    if texto:
        patron = patron_busqueda(texto)
        consulta = consulta.where(
            or_(
                Propietario.nombre.ilike(patron, escape="\\"),
                Propietario.numero_documento.ilike(patron, escape="\\"),
            )
        )
    return list(sesion.scalars(consulta))


def contar_apartaestudios_activos(sesion: Session, propietario_id: int) -> int:
    return sesion.scalar(
        select(func.count())
        .select_from(Apartaestudio)
        .where(Apartaestudio.propietario_id == propietario_id, Apartaestudio.activo.is_(True))
    )


# --- Apartaestudios -------------------------------------------------------------------------


def ocupado(hoy: date) -> ColumnElement[bool]:
    """RP-04: expresión SQL "el apartaestudio está ocupado hoy": tiene un contrato vigente,
    vencido o en terminación (RC-03)."""
    return contratos.apartaestudio_ocupado(Apartaestudio.id, hoy)


def tiene_contrato_reservado(sesion: Session, apartaestudio_id: int, hoy: date) -> bool:
    """Tiene un contrato por iniciar, vigente, vencido o en terminación (RP-07)."""
    return bool(sesion.scalar(select(contratos.apartaestudio_reservado(apartaestudio_id, hoy))))


def obtener_apartaestudio(
    sesion: Session, apartaestudio_id: int, *, bloquear: bool = False
) -> Apartaestudio | None:
    consulta = select(Apartaestudio).where(Apartaestudio.id == apartaestudio_id)
    if bloquear:
        # El bloqueo es solo de la fila del apartaestudio (no del propietario unido).
        consulta = consulta.with_for_update(of=Apartaestudio).execution_options(
            populate_existing=True
        )
    return sesion.scalar(consulta)


def existe_codigo(sesion: Session, codigo: str, excepto_id: int | None = None) -> bool:
    consulta = select(Apartaestudio.id).where(Apartaestudio.codigo == codigo)
    if excepto_id is not None:
        consulta = consulta.where(Apartaestudio.id != excepto_id)
    return sesion.scalar(consulta) is not None


def listar_apartaestudios(
    sesion: Session,
    *,
    hoy: date,
    propietario_id: int | None = None,
    ocupado_hoy: bool | None = None,
    en_mantenimiento: bool | None = None,
    activo: bool | None = None,
    texto: str | None = None,
    ids: list[int] | None = None,
) -> list[tuple[Apartaestudio, bool]]:
    """Apartaestudios con su ocupación, calculada en la misma consulta."""
    expresion = ocupado(hoy)
    consulta = select(Apartaestudio, expresion.label("ocupado")).order_by(Apartaestudio.codigo)
    if ids is not None:
        consulta = consulta.where(Apartaestudio.id.in_(ids))
    if propietario_id is not None:
        consulta = consulta.where(Apartaestudio.propietario_id == propietario_id)
    if ocupado_hoy is not None:
        consulta = consulta.where(expresion.is_(ocupado_hoy))
    if en_mantenimiento is not None:
        consulta = consulta.where(Apartaestudio.en_mantenimiento == en_mantenimiento)
    if activo is not None:
        consulta = consulta.where(Apartaestudio.activo == activo)
    if texto:
        patron = patron_busqueda(texto)
        consulta = consulta.where(
            or_(
                Apartaestudio.codigo.ilike(patron, escape="\\"),
                Apartaestudio.direccion.ilike(patron, escape="\\"),
            )
        )
    return [(fila[0], bool(fila[1])) for fila in sesion.execute(consulta)]
