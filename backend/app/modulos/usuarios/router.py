"""Gestión de usuarios: /usuarios/* (solo administrador)."""

from fastapi import APIRouter, Depends

from app.api.dependencias import BD, IP, Reloj
from app.modulos.usuarios import servicio
from app.modulos.usuarios.dependencias import SesionAdministrador, requiere_rol
from app.modulos.usuarios.esquemas import (
    RestablecerContrasena,
    UsuarioCrear,
    UsuarioEditar,
    UsuarioSalida,
)
from app.modulos.usuarios.modelos import Rol

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(requiere_rol(Rol.ADMINISTRADOR))],
)


@router.get("", response_model=list[UsuarioSalida], summary="Listar usuarios")
def listar(bd: BD, rol: Rol | None = None, activo: bool | None = None):
    return servicio.listar(bd, rol=rol, activo=activo)


@router.post("", response_model=UsuarioSalida, status_code=201, summary="Crear usuario")
def crear(datos: UsuarioCrear, actual: SesionAdministrador, bd: BD, ip: IP):
    return servicio.crear(bd, datos, actor_id=actual.usuario_id, ip=ip)


@router.get("/{usuario_id}", response_model=UsuarioSalida, summary="Detalle de un usuario")
def detalle(usuario_id: int, bd: BD):
    return servicio.obtener(bd, usuario_id)


@router.patch("/{usuario_id}", response_model=UsuarioSalida, summary="Editar usuario")
def editar(
    usuario_id: int, datos: UsuarioEditar, actual: SesionAdministrador, bd: BD, ip: IP, reloj: Reloj
):
    return servicio.editar(bd, usuario_id, datos, actor_id=actual.usuario_id, ip=ip, ahora=reloj())


@router.post("/{usuario_id}/desactivar", response_model=UsuarioSalida, summary="Desactivar usuario")
def desactivar(usuario_id: int, actual: SesionAdministrador, bd: BD, ip: IP, reloj: Reloj):
    return servicio.desactivar(bd, usuario_id, actor_id=actual.usuario_id, ip=ip, ahora=reloj())


@router.post("/{usuario_id}/activar", response_model=UsuarioSalida, summary="Reactivar usuario")
def activar(usuario_id: int, actual: SesionAdministrador, bd: BD, ip: IP):
    return servicio.activar(bd, usuario_id, actor_id=actual.usuario_id, ip=ip)


@router.post(
    "/{usuario_id}/restablecer-contrasena",
    response_model=UsuarioSalida,
    summary="Asignar una contraseña temporal",
)
def restablecer_contrasena(
    usuario_id: int,
    datos: RestablecerContrasena,
    actual: SesionAdministrador,
    bd: BD,
    ip: IP,
    reloj: Reloj,
):
    return servicio.restablecer_contrasena(
        bd,
        usuario_id,
        datos.contrasena_temporal,
        actor_id=actual.usuario_id,
        ip=ip,
        ahora=reloj(),
    )
