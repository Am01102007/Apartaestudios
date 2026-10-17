"""Gestión de usuarios: /usuarios/* (solo administrador).

Cada endpoint que modifica es el punto de entrada de su caso de uso: confirma la transacción
con `bd.commit()` cuando el servicio termina sin error.
"""

from fastapi import APIRouter, Depends

from app.api.dependencias import BD, IP, Reloj
from app.modulos.usuarios import servicio
from app.modulos.usuarios.dependencias import SesionAdministrador, solo_administrador
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
    dependencies=[Depends(solo_administrador)],
)


@router.get("", response_model=list[UsuarioSalida], summary="Listar usuarios")
def listar(bd: BD, rol: Rol | None = None, activo: bool | None = None):
    return servicio.listar(bd, rol=rol, activo=activo)


@router.post("", response_model=UsuarioSalida, status_code=201, summary="Crear usuario")
def crear(datos: UsuarioCrear, actual: SesionAdministrador, bd: BD, ip: IP):
    usuario = servicio.crear(bd, datos, actor_id=actual.usuario_id, ip=ip)
    bd.commit()
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioSalida, summary="Detalle de un usuario")
def detalle(usuario_id: int, bd: BD):
    return servicio.obtener(bd, usuario_id)


@router.patch("/{usuario_id}", response_model=UsuarioSalida, summary="Editar usuario")
def editar(
    usuario_id: int, datos: UsuarioEditar, actual: SesionAdministrador, bd: BD, ip: IP, reloj: Reloj
):
    usuario = servicio.editar(
        bd, usuario_id, datos, actor_id=actual.usuario_id, ip=ip, ahora=reloj()
    )
    bd.commit()
    return usuario


@router.post("/{usuario_id}/desactivar", response_model=UsuarioSalida, summary="Desactivar usuario")
def desactivar(usuario_id: int, actual: SesionAdministrador, bd: BD, ip: IP, reloj: Reloj):
    usuario = servicio.desactivar(bd, usuario_id, actor_id=actual.usuario_id, ip=ip, ahora=reloj())
    bd.commit()
    return usuario


@router.post("/{usuario_id}/activar", response_model=UsuarioSalida, summary="Reactivar usuario")
def activar(usuario_id: int, actual: SesionAdministrador, bd: BD, ip: IP):
    usuario = servicio.activar(bd, usuario_id, actor_id=actual.usuario_id, ip=ip)
    bd.commit()
    return usuario


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
    usuario = servicio.restablecer_contrasena(
        bd,
        usuario_id,
        datos.contrasena_temporal,
        actor_id=actual.usuario_id,
        ip=ip,
        ahora=reloj(),
    )
    bd.commit()
    return usuario
