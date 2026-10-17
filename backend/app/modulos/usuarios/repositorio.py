from datetime import datetime

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.modulos.usuarios.modelos import Rol, Sesion, Usuario


def obtener(sesion: Session, usuario_id: int, *, bloquear: bool = False) -> Usuario | None:
    consulta = select(Usuario).where(Usuario.id == usuario_id)
    if bloquear:
        # populate_existing: tras esperar el bloqueo, se leen los valores ya confirmados.
        consulta = consulta.with_for_update().execution_options(populate_existing=True)
    return sesion.scalar(consulta)


def obtener_por_nombre_usuario(
    sesion: Session, nombre_usuario: str, *, bloquear: bool = False
) -> Usuario | None:
    consulta = select(Usuario).where(Usuario.nombre_usuario == nombre_usuario)
    if bloquear:
        consulta = consulta.with_for_update().execution_options(populate_existing=True)
    return sesion.scalar(consulta)


def existe_nombre_usuario(
    sesion: Session, nombre_usuario: str, excepto_id: int | None = None
) -> bool:
    consulta = select(Usuario.id).where(Usuario.nombre_usuario == nombre_usuario)
    if excepto_id is not None:
        consulta = consulta.where(Usuario.id != excepto_id)
    return sesion.scalar(consulta) is not None


def listar(sesion: Session, *, rol: Rol | None, activo: bool | None) -> list[Usuario]:
    consulta = select(Usuario).order_by(Usuario.nombre)
    if rol is not None:
        consulta = consulta.where(Usuario.rol == rol)
    if activo is not None:
        consulta = consulta.where(Usuario.activo == activo)
    return list(sesion.scalars(consulta))


def bloquear_administradores_activos(sesion: Session) -> int:
    """Cuenta los administradores activos bloqueando sus filas hasta el fin de la transacción.

    El bloqueo evita que dos administradores se desactiven entre sí al mismo tiempo y dejen el
    sistema sin ninguno (RU-04). Las filas se bloquean siempre en orden de id para que dos
    peticiones simultáneas no se esperen mutuamente (bloqueo mutuo).
    """
    ids = sesion.scalars(
        select(Usuario.id)
        .where(Usuario.rol == Rol.ADMINISTRADOR, Usuario.activo.is_(True))
        .order_by(Usuario.id)
        .with_for_update()
    ).all()
    return len(ids)


def obtener_sesion(sesion: Session, id_sesion: str) -> Sesion | None:
    return sesion.get(Sesion, id_sesion)


def cerrar_sesiones(
    sesion: Session,
    usuario_id: int,
    motivo: str,
    ahora: datetime,
    excepto_id: str | None = None,
) -> int:
    consulta = (
        update(Sesion)
        .where(Sesion.usuario_id == usuario_id, Sesion.cerrada_en.is_(None))
        .values(cerrada_en=ahora, motivo_cierre=motivo)
    )
    if excepto_id is not None:
        consulta = consulta.where(Sesion.id != excepto_id)
    return sesion.execute(consulta).rowcount


def purgar_sesiones(sesion: Session, antes_de: datetime) -> int:
    """Borra las sesiones cerradas o vencidas antes de la fecha dada."""
    consulta = delete(Sesion).where(or_(Sesion.cerrada_en < antes_de, Sesion.expira_en < antes_de))
    return sesion.execute(consulta).rowcount
