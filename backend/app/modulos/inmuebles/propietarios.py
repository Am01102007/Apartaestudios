"""Gestión de propietarios (RF-03).

Como en todo el sistema, las funciones validan, modifican y auditan, pero no confirman: lo
hace el endpoint (ver app.db.sesion).
"""

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.errores import DatosInvalidos, NoEncontrado, ReglaDeNegocio
from app.modulos.auditoria import servicio as auditoria
from app.modulos.inmuebles import repositorio
from app.modulos.inmuebles.comun import cambios_de, guardar, instantanea
from app.modulos.inmuebles.esquemas import PropietarioCrear, PropietarioEditar
from app.modulos.inmuebles.modelos import Ocupacion, Propietario, TipoDocumento

ENTIDAD = "propietario"
CAMPOS_AUDITADOS = (
    "nombre",
    "tipo_documento",
    "numero_documento",
    "telefono",
    "correo",
    "direccion",
    "notas",
    "activo",
)


def _duplicado(tipo: TipoDocumento, numero: str) -> ReglaDeNegocio:
    return ReglaDeNegocio(
        f"Ya existe un propietario con el documento {tipo} {numero}.",
        codigo="documento_duplicado",
    )


def obtener(sesion: Session, propietario_id: int, *, bloquear: bool = False) -> Propietario:
    propietario = repositorio.obtener_propietario(sesion, propietario_id, bloquear=bloquear)
    if propietario is None:
        raise NoEncontrado("El propietario no existe.")
    return propietario


def listar(
    sesion: Session, *, activo: bool | None = None, texto: str | None = None
) -> list[Propietario]:
    return repositorio.listar_propietarios(sesion, activo=activo, texto=texto)


def detalle(sesion: Session, propietario_id: int, *, hoy: date) -> dict[str, Any]:
    """P-03: el propietario con sus apartaestudios y la ocupación de cada uno."""
    propietario = obtener(sesion, propietario_id)
    filas = repositorio.listar_apartaestudios(sesion, hoy=hoy, propietario_id=propietario.id)
    return {
        **instantanea(propietario, ("id", *CAMPOS_AUDITADOS, "creado_en")),
        "apartaestudios": [
            {
                **instantanea(a, ("id", "codigo", "direccion", "activo", "en_mantenimiento")),
                "ocupacion": Ocupacion.OCUPADO if ocupado else Ocupacion.LIBRE,
            }
            for a, ocupado in filas
        ],
    }


def crear(
    sesion: Session, datos: PropietarioCrear, *, actor_id: int | None, ip: str | None
) -> Propietario:
    if repositorio.existe_documento(sesion, datos.tipo_documento, datos.numero_documento):
        raise _duplicado(datos.tipo_documento, datos.numero_documento)

    propietario = Propietario(**datos.model_dump(), activo=True)
    sesion.add(propietario)
    guardar(sesion, _duplicado(datos.tipo_documento, datos.numero_documento))

    auditoria.registrar(
        sesion,
        accion="propietario.crear",
        entidad=ENTIDAD,
        entidad_id=propietario.id,
        usuario_id=actor_id,
        despues=instantanea(propietario, CAMPOS_AUDITADOS),
        ip=ip,
    )
    return propietario


def editar(
    sesion: Session,
    propietario_id: int,
    datos: PropietarioEditar,
    *,
    actor_id: int,
    ip: str | None,
) -> Propietario:
    propietario = obtener(sesion, propietario_id, bloquear=True)
    cambios = cambios_de(propietario, datos.model_dump(exclude_unset=True))
    if not cambios:
        return propietario

    tipo = cambios.get("tipo_documento", propietario.tipo_documento)
    numero = cambios.get("numero_documento", propietario.numero_documento)
    if tipo in (TipoDocumento.CC, TipoDocumento.NIT) and not numero.isdigit():
        raise DatosInvalidos(
            f"El número de {tipo} solo puede tener dígitos.",
            [{"campo": "numero_documento", "mensaje": "Solo dígitos"}],
        )
    if ("tipo_documento" in cambios or "numero_documento" in cambios) and (
        repositorio.existe_documento(sesion, tipo, numero, excepto_id=propietario.id)
    ):
        raise _duplicado(tipo, numero)

    antes = instantanea(propietario, tuple(cambios))
    for campo, valor in cambios.items():
        setattr(propietario, campo, valor)
    guardar(sesion, _duplicado(tipo, numero))

    auditoria.registrar(
        sesion,
        accion="propietario.editar",
        entidad=ENTIDAD,
        entidad_id=propietario.id,
        usuario_id=actor_id,
        antes=antes,
        despues=instantanea(propietario, tuple(cambios)),
        ip=ip,
    )
    return propietario


def desactivar(
    sesion: Session, propietario_id: int, *, actor_id: int, ip: str | None
) -> Propietario:
    """P-10. La fila del propietario queda bloqueada, así que nadie puede crear, activar ni
    pasarle un apartaestudio mientras se cuenta (esas operaciones también lo bloquean)."""
    propietario = obtener(sesion, propietario_id, bloquear=True)
    if not propietario.activo:
        return propietario
    activos = repositorio.contar_apartaestudios_activos(sesion, propietario.id)
    if activos:
        raise ReglaDeNegocio(
            f"El propietario tiene {activos} apartaestudio(s) activo(s). Desactívalos o "
            "asígnalos a otro propietario primero.",
            codigo="propietario_con_apartaestudios",
        )
    propietario.activo = False
    auditoria.registrar(
        sesion,
        accion="propietario.desactivar",
        entidad=ENTIDAD,
        entidad_id=propietario.id,
        usuario_id=actor_id,
        antes={"activo": True},
        despues={"activo": False},
        ip=ip,
    )
    return propietario


def activar(sesion: Session, propietario_id: int, *, actor_id: int, ip: str | None) -> Propietario:
    propietario = obtener(sesion, propietario_id, bloquear=True)
    if propietario.activo:
        return propietario
    propietario.activo = True
    auditoria.registrar(
        sesion,
        accion="propietario.activar",
        entidad=ENTIDAD,
        entidad_id=propietario.id,
        usuario_id=actor_id,
        antes={"activo": False},
        despues={"activo": True},
        ip=ip,
    )
    return propietario
