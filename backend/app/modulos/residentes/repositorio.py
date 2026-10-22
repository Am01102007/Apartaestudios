from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.documentos import TipoDocumento, normalizar_documento
from app.db.consultas import patron_busqueda
from app.modulos.residentes.modelos import Residente


def obtener(sesion: Session, residente_id: int, *, bloquear: bool = False) -> Residente | None:
    consulta = select(Residente).where(Residente.id == residente_id)
    if bloquear:
        consulta = consulta.with_for_update().execution_options(populate_existing=True)
    return sesion.scalar(consulta)


def existe_documento(
    sesion: Session, tipo: TipoDocumento, numero: str, excepto_id: int | None = None
) -> bool:
    consulta = select(Residente.id).where(
        Residente.tipo_documento == tipo, Residente.numero_documento == numero
    )
    if excepto_id is not None:
        consulta = consulta.where(Residente.id != excepto_id)
    return sesion.scalar(consulta) is not None


def listar(sesion: Session, *, texto: str | None) -> list[Residente]:
    consulta = select(Residente).order_by(Residente.nombre, Residente.id)
    if texto:
        consulta = consulta.where(
            or_(
                Residente.nombre.ilike(patron_busqueda(texto), escape="\\"),
                Residente.numero_documento.ilike(
                    patron_busqueda(normalizar_documento(texto)), escape="\\"
                ),
            )
        )
    return list(sesion.scalars(consulta))
