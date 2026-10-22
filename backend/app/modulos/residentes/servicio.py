"""Directorio de residentes (RF-06).

Las funciones validan, modifican y auditan, pero no confirman: lo hace el endpoint.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.documentos import TipoDocumento, error_documento
from app.core.errores import DatosInvalidos, NoEncontrado, ReglaDeNegocio
from app.modulos.auditoria import servicio as auditoria
from app.modulos.bloqueos import servicio as bloqueos
from app.modulos.bloqueos.modelos import Bloqueo
from app.modulos.residentes import repositorio
from app.modulos.residentes.esquemas import ResidenteCrear, ResidenteEditar
from app.modulos.residentes.modelos import Residente

ENTIDAD = "residente"
CAMPOS_AUDITADOS = (
    "nombre",
    "tipo_documento",
    "numero_documento",
    "telefono",
    "correo",
    "contacto_emergencia_nombre",
    "contacto_emergencia_telefono",
    "notas",
)


def _duplicado(tipo: TipoDocumento, numero: str) -> ReglaDeNegocio:
    return ReglaDeNegocio(
        f"Ya existe un residente con el documento {tipo} {numero}.", codigo="documento_duplicado"
    )


def _guardar(sesion: Session, tipo: TipoDocumento, numero: str) -> None:
    """flush en un punto de guardado: un documento duplicado que llegó al mismo tiempo lo
    detiene la restricción única y se informa como regla de negocio."""
    try:
        with sesion.begin_nested():
            sesion.flush()
    except IntegrityError as exc:
        raise _duplicado(tipo, numero) from exc


def _instantanea(residente: Residente, campos=CAMPOS_AUDITADOS) -> dict:
    return {campo: getattr(residente, campo) for campo in campos}


def obtener(sesion: Session, residente_id: int, *, bloquear: bool = False) -> Residente:
    residente = repositorio.obtener(sesion, residente_id, bloquear=bloquear)
    if residente is None:
        raise NoEncontrado("El residente no existe.")
    return residente


def detalle(sesion: Session, residente_id: int) -> tuple[Residente, Bloqueo | None]:
    """R-04: el residente y su bloqueo activo, si tiene (se busca por su documento)."""
    residente = obtener(sesion, residente_id)
    return residente, bloqueos.bloqueo_activo(
        sesion, residente.tipo_documento, residente.numero_documento
    )


def listar(sesion: Session, *, texto: str | None = None) -> list[Residente]:
    return repositorio.listar(sesion, texto=texto)


def crear(
    sesion: Session, datos: ResidenteCrear, *, actor_id: int | None, ip: str | None
) -> Residente:
    tipo, numero = datos.tipo_documento, datos.numero_documento
    if repositorio.existe_documento(sesion, tipo, numero):
        raise _duplicado(tipo, numero)
    residente = Residente(**datos.model_dump())
    sesion.add(residente)
    _guardar(sesion, tipo, numero)
    auditoria.registrar(
        sesion,
        accion="residente.crear",
        entidad=ENTIDAD,
        entidad_id=residente.id,
        usuario_id=actor_id,
        despues=_instantanea(residente),
        ip=ip,
    )
    return residente


def editar(
    sesion: Session, residente_id: int, datos: ResidenteEditar, *, actor_id: int, ip: str | None
) -> Residente:
    residente = obtener(sesion, residente_id, bloquear=True)
    cambios = {
        campo: valor
        for campo, valor in datos.model_dump(exclude_unset=True).items()
        if getattr(residente, campo) != valor
    }
    if not cambios:
        return residente

    tipo = cambios.get("tipo_documento", residente.tipo_documento)
    numero = cambios.get("numero_documento", residente.numero_documento)
    if mensaje := error_documento(tipo, numero):
        raise DatosInvalidos(f"{mensaje}.", [{"campo": "numero_documento", "mensaje": mensaje}])
    contacto = (
        cambios.get("contacto_emergencia_nombre", residente.contacto_emergencia_nombre),
        cambios.get("contacto_emergencia_telefono", residente.contacto_emergencia_telefono),
    )
    if (contacto[0] is None) != (contacto[1] is None):
        raise DatosInvalidos(
            "El contacto de emergencia necesita nombre y teléfono.",
            [{"campo": "contacto_emergencia", "mensaje": "Incompleto"}],
        )
    if ("tipo_documento" in cambios or "numero_documento" in cambios) and (
        repositorio.existe_documento(sesion, tipo, numero, excepto_id=residente.id)
    ):
        raise _duplicado(tipo, numero)

    antes = _instantanea(residente, tuple(cambios))
    for campo, valor in cambios.items():
        setattr(residente, campo, valor)
    _guardar(sesion, tipo, numero)
    auditoria.registrar(
        sesion,
        accion="residente.editar",
        entidad=ENTIDAD,
        entidad_id=residente.id,
        usuario_id=actor_id,
        antes=antes,
        despues=_instantanea(residente, tuple(cambios)),
        ip=ip,
    )
    return residente
