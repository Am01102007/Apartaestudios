"""Gestión de usuarios por el administrador (RF-02).

Cada función es un caso de uso completo: valida las reglas, modifica, audita y confirma la
transacción. Si algo falla, nada queda guardado.
"""

from datetime import datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errores import DatosInvalidos, NoEncontrado, ReglaDeNegocio
from app.core.seguridad import hashear_contrasena
from app.modulos.auditoria import servicio as auditoria
from app.modulos.usuarios import repositorio
from app.modulos.usuarios.esquemas import UsuarioCrear, UsuarioEditar
from app.modulos.usuarios.modelos import MotivoCierre, Rol, Usuario

ENTIDAD = "usuario"
CAMPOS_AUDITADOS = (
    "nombre_usuario",
    "nombre",
    "correo",
    "rol",
    "activo",
    "debe_cambiar_contrasena",
)


def instantanea(usuario: Usuario) -> dict[str, Any]:
    return {campo: getattr(usuario, campo) for campo in CAMPOS_AUDITADOS}


def validar_contrasena(contrasena: str, nombre_usuario: str) -> None:
    """RU-06. La longitud la valida el esquema; aquí, lo que depende de otros datos."""
    if contrasena.strip().lower() == nombre_usuario.lower():
        raise DatosInvalidos(
            "La contraseña no puede ser igual al nombre de usuario.",
            [{"campo": "contrasena", "mensaje": "Igual al nombre de usuario"}],
        )


def _usuario_duplicado(nombre_usuario: str) -> ReglaDeNegocio:
    return ReglaDeNegocio(
        f"El nombre de usuario «{nombre_usuario}» ya está registrado.",
        codigo="usuario_duplicado",
    )


def obtener(sesion: Session, usuario_id: int) -> Usuario:
    usuario = repositorio.obtener(sesion, usuario_id)
    if usuario is None:
        raise NoEncontrado("El usuario no existe.")
    return usuario


def listar(sesion: Session, *, rol: Rol | None = None, activo: bool | None = None) -> list[Usuario]:
    return repositorio.listar(sesion, rol=rol, activo=activo)


def crear(
    sesion: Session,
    datos: UsuarioCrear,
    *,
    actor_id: int | None,
    ip: str | None,
    debe_cambiar_contrasena: bool = True,
) -> Usuario:
    """Crea un usuario. Por defecto, con contraseña temporal que debe cambiar al entrar."""
    validar_contrasena(datos.contrasena_temporal, datos.nombre_usuario)
    if repositorio.existe_nombre_usuario(sesion, datos.nombre_usuario):
        raise _usuario_duplicado(datos.nombre_usuario)

    usuario = Usuario(
        nombre_usuario=datos.nombre_usuario,
        nombre=datos.nombre,
        correo=datos.correo,
        rol=datos.rol,
        hash_contrasena=hashear_contrasena(datos.contrasena_temporal),
        activo=True,
        debe_cambiar_contrasena=debe_cambiar_contrasena,
        intentos_fallidos=0,
    )
    sesion.add(usuario)
    try:
        sesion.flush()
    except IntegrityError as exc:  # otra petición creó el mismo nombre al mismo tiempo
        sesion.rollback()
        raise _usuario_duplicado(datos.nombre_usuario) from exc

    auditoria.registrar(
        sesion,
        accion="usuario.crear",
        entidad=ENTIDAD,
        entidad_id=usuario.id,
        usuario_id=actor_id,
        despues=instantanea(usuario),
        ip=ip,
    )
    sesion.commit()
    return usuario


def _exigir_otro_administrador(sesion: Session) -> None:
    """RU-04: no dejar el sistema sin administradores activos."""
    if repositorio.bloquear_administradores_activos(sesion) <= 1:
        raise ReglaDeNegocio(
            "Debe quedar al menos un administrador activo.", codigo="ultimo_administrador"
        )


def editar(
    sesion: Session,
    usuario_id: int,
    datos: UsuarioEditar,
    *,
    actor_id: int,
    ip: str | None,
    ahora: datetime,
) -> Usuario:
    usuario = repositorio.obtener(sesion, usuario_id, bloquear=True)
    if usuario is None:
        raise NoEncontrado("El usuario no existe.")

    cambios = {
        campo: valor
        for campo, valor in datos.model_dump(exclude_unset=True).items()
        if getattr(usuario, campo) != valor
    }
    if not cambios:
        return usuario

    if "nombre_usuario" in cambios and repositorio.existe_nombre_usuario(
        sesion, cambios["nombre_usuario"], excepto_id=usuario.id
    ):
        raise _usuario_duplicado(cambios["nombre_usuario"])

    cambia_rol = "rol" in cambios
    if cambia_rol:
        if usuario.id == actor_id:
            raise ReglaDeNegocio("No puedes cambiar tu propio rol.", codigo="accion_sobre_si_mismo")
        if usuario.es_administrador and usuario.activo:
            _exigir_otro_administrador(sesion)

    antes = instantanea(usuario)
    for campo, valor in cambios.items():
        setattr(usuario, campo, valor)
    if cambia_rol:
        # Las sesiones abiertas se emitieron con el rol anterior.
        repositorio.cerrar_sesiones(sesion, usuario.id, MotivoCierre.CAMBIO_ROL, ahora)

    try:
        sesion.flush()
    except IntegrityError as exc:
        sesion.rollback()
        raise _usuario_duplicado(cambios.get("nombre_usuario", "")) from exc

    auditoria.registrar(
        sesion,
        accion="usuario.editar",
        entidad=ENTIDAD,
        entidad_id=usuario.id,
        usuario_id=actor_id,
        antes={campo: antes[campo] for campo in cambios},
        despues={campo: getattr(usuario, campo) for campo in cambios},
        ip=ip,
    )
    sesion.commit()
    return usuario


def desactivar(
    sesion: Session, usuario_id: int, *, actor_id: int, ip: str | None, ahora: datetime
) -> Usuario:
    usuario = repositorio.obtener(sesion, usuario_id, bloquear=True)
    if usuario is None:
        raise NoEncontrado("El usuario no existe.")
    if not usuario.activo:
        return usuario
    if usuario.id == actor_id:
        raise ReglaDeNegocio(
            "No puedes desactivar tu propio usuario.", codigo="accion_sobre_si_mismo"
        )
    if usuario.es_administrador:
        _exigir_otro_administrador(sesion)

    usuario.activo = False
    cerradas = repositorio.cerrar_sesiones(sesion, usuario.id, MotivoCierre.DESACTIVADO, ahora)
    auditoria.registrar(
        sesion,
        accion="usuario.desactivar",
        entidad=ENTIDAD,
        entidad_id=usuario.id,
        usuario_id=actor_id,
        antes={"activo": True},
        despues={"activo": False, "sesiones_cerradas": cerradas},
        ip=ip,
    )
    sesion.commit()
    return usuario


def activar(sesion: Session, usuario_id: int, *, actor_id: int, ip: str | None) -> Usuario:
    usuario = repositorio.obtener(sesion, usuario_id, bloquear=True)
    if usuario is None:
        raise NoEncontrado("El usuario no existe.")
    if usuario.activo:
        return usuario

    usuario.activo = True
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    auditoria.registrar(
        sesion,
        accion="usuario.activar",
        entidad=ENTIDAD,
        entidad_id=usuario.id,
        usuario_id=actor_id,
        antes={"activo": False},
        despues={"activo": True},
        ip=ip,
    )
    sesion.commit()
    return usuario


def restablecer_contrasena(
    sesion: Session,
    usuario_id: int,
    contrasena_temporal: str,
    *,
    actor_id: int,
    ip: str | None,
    ahora: datetime,
) -> Usuario:
    """RU-09: contraseña temporal asignada por el administrador; se cambia al entrar."""
    usuario = repositorio.obtener(sesion, usuario_id, bloquear=True)
    if usuario is None:
        raise NoEncontrado("El usuario no existe.")
    validar_contrasena(contrasena_temporal, usuario.nombre_usuario)

    usuario.hash_contrasena = hashear_contrasena(contrasena_temporal)
    usuario.debe_cambiar_contrasena = True
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    cerradas = repositorio.cerrar_sesiones(sesion, usuario.id, MotivoCierre.RESTABLECIMIENTO, ahora)
    auditoria.registrar(
        sesion,
        accion="usuario.restablecer_contrasena",
        entidad=ENTIDAD,
        entidad_id=usuario.id,
        usuario_id=actor_id,
        despues={"debe_cambiar_contrasena": True, "sesiones_cerradas": cerradas},
        ip=ip,
    )
    sesion.commit()
    return usuario
