"""Gestión de apartaestudios (RF-04, RF-05).

Orden de bloqueos, siempre el mismo para que dos peticiones no se esperen mutuamente:
primero el apartaestudio y después sus propietarios, en orden de id. Toda operación que
crea, activa o pasa un apartaestudio a un propietario bloquea a ese propietario, y
desactivar un propietario también lo bloquea: así no se cruzan (P-10).
"""

from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errores import NoEncontrado, ReglaDeNegocio
from app.modulos.auditoria import servicio as auditoria
from app.modulos.inmuebles import repositorio
from app.modulos.inmuebles.comun import cambios_de, guardar, instantanea
from app.modulos.inmuebles.esquemas import ApartaestudioCrear, ApartaestudioEditar
from app.modulos.inmuebles.modelos import Apartaestudio, Ocupacion, Propietario

ENTIDAD = "apartaestudio"
CAMPOS_AUDITADOS = (
    "codigo",
    "propietario_id",
    "direccion",
    "area_m2",
    "descripcion",
    "en_mantenimiento",
    "activo",
)


def _duplicado(codigo: str) -> ReglaDeNegocio:
    return ReglaDeNegocio(
        f"Ya existe un apartaestudio con el código «{codigo}».", codigo="codigo_duplicado"
    )


def _exigir_propietario_activo(propietario: Propietario | None) -> Propietario:
    if propietario is None or not propietario.activo:
        raise ReglaDeNegocio(
            "El propietario no existe o está inactivo.", codigo="propietario_no_valido"
        )
    return propietario


def _con_ocupacion(sesion: Session, apartaestudio: Apartaestudio, hoy: date) -> Apartaestudio:
    """Añade la ocupación calculada (RP-04) al objeto que devuelve el endpoint."""
    sesion.flush()
    ocupado = sesion.scalar(
        select(repositorio.ocupado(hoy)).where(Apartaestudio.id == apartaestudio.id)
    )
    apartaestudio.ocupacion = Ocupacion.OCUPADO if ocupado else Ocupacion.LIBRE
    return apartaestudio


def _obtener(sesion: Session, apartaestudio_id: int, *, bloquear: bool = False) -> Apartaestudio:
    apartaestudio = repositorio.obtener_apartaestudio(sesion, apartaestudio_id, bloquear=bloquear)
    if apartaestudio is None:
        raise NoEncontrado("El apartaestudio no existe.")
    return apartaestudio


def obtener(sesion: Session, apartaestudio_id: int, *, hoy: date) -> Apartaestudio:
    return _con_ocupacion(sesion, _obtener(sesion, apartaestudio_id), hoy)


def listar(
    sesion: Session,
    *,
    hoy: date,
    propietario_id: int | None = None,
    ocupacion: Ocupacion | None = None,
    en_mantenimiento: bool | None = None,
    activo: bool | None = None,
    texto: str | None = None,
) -> list[Apartaestudio]:
    filas = repositorio.listar_apartaestudios(
        sesion,
        hoy=hoy,
        propietario_id=propietario_id,
        ocupado_hoy=None if ocupacion is None else ocupacion == Ocupacion.OCUPADO,
        en_mantenimiento=en_mantenimiento,
        activo=activo,
        texto=texto,
    )
    for apartaestudio, ocupado in filas:
        apartaestudio.ocupacion = Ocupacion.OCUPADO if ocupado else Ocupacion.LIBRE
    return [apartaestudio for apartaestudio, _ in filas]


def crear(
    sesion: Session,
    datos: ApartaestudioCrear,
    *,
    actor_id: int | None,
    ip: str | None,
    hoy: date,
) -> Apartaestudio:
    _exigir_propietario_activo(
        repositorio.obtener_propietario(sesion, datos.propietario_id, bloquear=True)
    )
    if repositorio.existe_codigo(sesion, datos.codigo):
        raise _duplicado(datos.codigo)

    apartaestudio = Apartaestudio(**datos.model_dump(), activo=True, en_mantenimiento=False)
    sesion.add(apartaestudio)
    guardar(sesion, _duplicado(datos.codigo))

    auditoria.registrar(
        sesion,
        accion="apartaestudio.crear",
        entidad=ENTIDAD,
        entidad_id=apartaestudio.id,
        usuario_id=actor_id,
        despues=instantanea(apartaestudio, CAMPOS_AUDITADOS),
        ip=ip,
    )
    return _con_ocupacion(sesion, apartaestudio, hoy)


def editar(
    sesion: Session,
    apartaestudio_id: int,
    datos: ApartaestudioEditar,
    *,
    actor_id: int,
    ip: str | None,
    hoy: date,
) -> Apartaestudio:
    apartaestudio = _obtener(sesion, apartaestudio_id, bloquear=True)
    cambios = cambios_de(apartaestudio, datos.model_dump(exclude_unset=True))
    if not cambios:
        return _con_ocupacion(sesion, apartaestudio, hoy)

    if "propietario_id" in cambios:
        # RP-08: el cambio de propietario (por ejemplo, una venta) queda en la auditoría.
        bloqueados = repositorio.bloquear_propietarios(
            sesion, {apartaestudio.propietario_id, cambios["propietario_id"]}
        )
        _exigir_propietario_activo(bloqueados.get(cambios["propietario_id"]))
    if "codigo" in cambios and repositorio.existe_codigo(
        sesion, cambios["codigo"], excepto_id=apartaestudio.id
    ):
        raise _duplicado(cambios["codigo"])

    antes = instantanea(apartaestudio, tuple(cambios))
    for campo, valor in cambios.items():
        setattr(apartaestudio, campo, valor)
    guardar(sesion, _duplicado(apartaestudio.codigo))
    if "propietario_id" in cambios:
        sesion.refresh(apartaestudio, ["propietario"])

    auditoria.registrar(
        sesion,
        accion="apartaestudio.editar",
        entidad=ENTIDAD,
        entidad_id=apartaestudio.id,
        usuario_id=actor_id,
        antes=antes,
        despues=instantanea(apartaestudio, tuple(cambios)),
        ip=ip,
    )
    return _con_ocupacion(sesion, apartaestudio, hoy)


def cambiar_mantenimiento(
    sesion: Session,
    apartaestudio_id: int,
    *,
    activo: bool,
    motivo: str,
    actor_id: int,
    ip: str | None,
    ahora: datetime,
    hoy: date,
) -> Apartaestudio:
    """RP-05: marca independiente de la ocupación; activarla no impide contratos."""
    apartaestudio = _obtener(sesion, apartaestudio_id, bloquear=True)
    if activo == apartaestudio.en_mantenimiento:
        if activo:
            raise ReglaDeNegocio(
                "El apartaestudio ya está en mantenimiento.", codigo="ya_en_mantenimiento"
            )
        raise ReglaDeNegocio(
            "El apartaestudio no está en mantenimiento.", codigo="sin_mantenimiento"
        )

    antes = instantanea(
        apartaestudio, ("en_mantenimiento", "mantenimiento_desde", "mantenimiento_motivo")
    )
    apartaestudio.en_mantenimiento = activo
    apartaestudio.mantenimiento_desde = ahora if activo else None
    apartaestudio.mantenimiento_motivo = motivo if activo else None
    apartaestudio.mantenimiento_por_id = actor_id if activo else None

    auditoria.registrar(
        sesion,
        accion="apartaestudio.mantenimiento_activar"
        if activo
        else "apartaestudio.mantenimiento_retirar",
        entidad=ENTIDAD,
        entidad_id=apartaestudio.id,
        usuario_id=actor_id,
        antes=antes,
        despues={"en_mantenimiento": activo, "motivo": motivo},
        ip=ip,
    )
    return _con_ocupacion(sesion, apartaestudio, hoy)


def desactivar(
    sesion: Session, apartaestudio_id: int, *, actor_id: int, ip: str | None, hoy: date
) -> Apartaestudio:
    # RP-07: cuando existan los contratos, aquí se rechazará si tiene uno activo.
    apartaestudio = _obtener(sesion, apartaestudio_id, bloquear=True)
    if apartaestudio.activo:
        apartaestudio.activo = False
        auditoria.registrar(
            sesion,
            accion="apartaestudio.desactivar",
            entidad=ENTIDAD,
            entidad_id=apartaestudio.id,
            usuario_id=actor_id,
            antes={"activo": True},
            despues={"activo": False},
            ip=ip,
        )
    return _con_ocupacion(sesion, apartaestudio, hoy)


def activar(
    sesion: Session, apartaestudio_id: int, *, actor_id: int, ip: str | None, hoy: date
) -> Apartaestudio:
    apartaestudio = _obtener(sesion, apartaestudio_id, bloquear=True)
    if not apartaestudio.activo:
        propietario = repositorio.obtener_propietario(
            sesion, apartaestudio.propietario_id, bloquear=True
        )
        if propietario is None or not propietario.activo:
            raise ReglaDeNegocio(
                "Su propietario está inactivo. Actívalo o asigna otro propietario primero.",
                codigo="propietario_inactivo",
            )
        apartaestudio.activo = True
        auditoria.registrar(
            sesion,
            accion="apartaestudio.activar",
            entidad=ENTIDAD,
            entidad_id=apartaestudio.id,
            usuario_id=actor_id,
            antes={"activo": False},
            despues={"activo": True},
            ip=ip,
        )
    return _con_ocupacion(sesion, apartaestudio, hoy)
