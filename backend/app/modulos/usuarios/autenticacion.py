"""Inicio y cierre de sesión, validación de sesiones y cambio de la propia contraseña (RF-01).

Decisiones aplicadas (fase 6 y D-3):
- La cookie lleva un JWT firmado que solo identifica la sesión; la sesión vive en la tabla
  `sesiones`, de modo que cerrarla tiene efecto inmediato.
- La sesión vence tras 30 minutos sin uso o 12 horas desde el ingreso.
- 5 intentos fallidos seguidos bloquean el ingreso de la cuenta durante 15 minutos.

Como los demás servicios, no confirma la transacción; la confirma el endpoint. Las únicas
excepciones son las transacciones cortas de `validar_sesion`, que se ejecuta como dependencia
de todos los endpoints antes del caso de uso.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import Configuracion
from app.core.errores import NoAutenticado, ReglaDeNegocio
from app.core.seguridad import (
    crear_jwt,
    generar_token,
    hashear_contrasena,
    leer_jwt,
    requiere_rehash,
    resumen_token,
    tokens_iguales,
    verificar_contrasena,
)
from app.modulos.auditoria import servicio as auditoria
from app.modulos.usuarios import repositorio
from app.modulos.usuarios.modelos import MotivoCierre, Sesion, Usuario
from app.modulos.usuarios.servicio import ENTIDAD, validar_contrasena

MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."


class IngresoRechazado(NoAutenticado):
    """Ingreso rechazado cuyo rastro (intentos, bloqueo, auditoría) debe guardarse igual:
    quien llama confirma la transacción antes de devolver el error."""


# Frecuencia máxima con que se guarda el último uso, para no escribir en cada petición.
INTERVALO_REGISTRO_USO = timedelta(minutes=1)


@dataclass
class Ingreso:
    usuario: Usuario
    sesion: Sesion
    jwt: str
    token_csrf: str


def iniciar_sesion(
    bd: Session,
    nombre_usuario: str,
    contrasena: str,
    *,
    config: Configuracion,
    ahora: datetime,
    ip: str | None,
    agente_usuario: str | None,
) -> Ingreso:
    nombre_usuario = nombre_usuario.strip().lower()
    usuario = repositorio.obtener_por_nombre_usuario(bd, nombre_usuario, bloquear=True)

    if usuario is None:
        verificar_contrasena(None, contrasena)  # mismo tiempo de respuesta que un usuario real
        auditoria.registrar(
            bd,
            accion="sesion.ingreso_fallido",
            entidad=ENTIDAD,
            despues={"nombre_usuario": nombre_usuario[:30], "motivo": "usuario_inexistente"},
            ip=ip,
        )
        raise IngresoRechazado(MENSAJE_CREDENCIALES, codigo="credenciales_invalidas")

    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
        auditoria.registrar(
            bd,
            accion="sesion.ingreso_bloqueado",
            entidad=ENTIDAD,
            entidad_id=usuario.id,
            usuario_id=usuario.id,
            ip=ip,
        )
        raise IngresoRechazado(
            "La cuenta está bloqueada temporalmente por intentos fallidos. "
            f"Intenta de nuevo en {config.minutos_bloqueo} minutos.",
            codigo="cuenta_bloqueada",
        )

    if not verificar_contrasena(usuario.hash_contrasena, contrasena):
        usuario.intentos_fallidos += 1
        detalle = {"intentos_fallidos": usuario.intentos_fallidos}
        if usuario.intentos_fallidos >= config.intentos_fallidos_maximos:
            usuario.bloqueado_hasta = ahora + timedelta(minutes=config.minutos_bloqueo)
            usuario.intentos_fallidos = 0
            detalle["bloqueado_hasta"] = usuario.bloqueado_hasta
        auditoria.registrar(
            bd,
            accion="sesion.ingreso_fallido",
            entidad=ENTIDAD,
            entidad_id=usuario.id,
            usuario_id=usuario.id,
            despues=detalle,
            ip=ip,
        )
        raise IngresoRechazado(MENSAJE_CREDENCIALES, codigo="credenciales_invalidas")

    # El estado inactivo se revela solo a quien conoce la contraseña.
    if not usuario.activo:
        raise NoAutenticado(
            "Tu usuario está desactivado. Contacta al administrador.", codigo="usuario_inactivo"
        )

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_ingreso = ahora
    if requiere_rehash(usuario.hash_contrasena):
        usuario.hash_contrasena = hashear_contrasena(contrasena)

    token_csrf = generar_token()
    sesion = Sesion(
        id=generar_token(),
        usuario_id=usuario.id,
        hash_csrf=resumen_token(token_csrf),
        creada_en=ahora,
        ultimo_uso=ahora,
        expira_en=ahora + timedelta(hours=config.horas_maximas_sesion),
        ip=ip,
        agente_usuario=(agente_usuario or "")[:255] or None,
    )
    bd.add(sesion)
    auditoria.registrar(
        bd,
        accion="sesion.ingreso",
        entidad=ENTIDAD,
        entidad_id=usuario.id,
        usuario_id=usuario.id,
        ip=ip,
    )
    bd.flush()
    jwt = crear_jwt(config.clave_jwt, sesion.id, usuario.id, ahora, sesion.expira_en)
    return Ingreso(usuario=usuario, sesion=sesion, jwt=jwt, token_csrf=token_csrf)


def validar_sesion(
    bd: Session,
    token: str | None,
    *,
    config: Configuracion,
    ahora: datetime,
) -> Sesion:
    """Devuelve la sesión abierta del token, o lanza NoAutenticado."""
    sin_sesion = NoAutenticado("Debes iniciar sesión.", codigo="sesion_invalida")
    if not token:
        raise sin_sesion
    datos = leer_jwt(config.clave_jwt, token, ahora)
    if datos is None:
        raise sin_sesion

    sesion = repositorio.obtener_sesion(bd, datos["sid"])
    if (
        sesion is None
        or str(sesion.usuario_id) != datos["sub"]
        or sesion.cerrada_en is not None
        or sesion.expira_en <= ahora
        or not sesion.usuario.activo
    ):
        raise sin_sesion

    if sesion.ultimo_uso + timedelta(minutes=config.minutos_inactividad) <= ahora:
        sesion.cerrada_en = ahora
        sesion.motivo_cierre = MotivoCierre.INACTIVIDAD
        bd.commit()  # transacción corta propia: el cierre se guarda aunque la petición falle
        raise NoAutenticado(
            "La sesión expiró por inactividad. Inicia sesión de nuevo.", codigo="sesion_expirada"
        )

    if ahora - sesion.ultimo_uso >= INTERVALO_REGISTRO_USO:
        sesion.ultimo_uso = ahora
        bd.commit()  # transacción corta propia, antes de empezar el caso de uso
    return sesion


def csrf_valido(sesion: Sesion, token_csrf: str | None) -> bool:
    return bool(token_csrf) and tokens_iguales(token_csrf, sesion.hash_csrf)


def cerrar_sesion(bd: Session, sesion: Sesion, *, ahora: datetime, ip: str | None) -> None:
    sesion.cerrada_en = ahora
    sesion.motivo_cierre = MotivoCierre.LOGOUT
    auditoria.registrar(
        bd,
        accion="sesion.cierre",
        entidad=ENTIDAD,
        entidad_id=sesion.usuario_id,
        usuario_id=sesion.usuario_id,
        ip=ip,
    )


def cambiar_contrasena(
    bd: Session,
    sesion: Sesion,
    contrasena_actual: str,
    contrasena_nueva: str,
    *,
    ahora: datetime,
    ip: str | None,
) -> None:
    usuario = repositorio.obtener(bd, sesion.usuario_id, bloquear=True)
    if usuario is None or not verificar_contrasena(usuario.hash_contrasena, contrasena_actual):
        raise ReglaDeNegocio(
            "La contraseña actual no es correcta.", codigo="contrasena_actual_incorrecta"
        )
    if contrasena_nueva == contrasena_actual:
        raise ReglaDeNegocio(
            "La nueva contraseña debe ser distinta de la actual.", codigo="contrasena_repetida"
        )
    validar_contrasena(contrasena_nueva, usuario.nombre_usuario)

    usuario.hash_contrasena = hashear_contrasena(contrasena_nueva)
    usuario.debe_cambiar_contrasena = False
    cerradas = repositorio.cerrar_sesiones(
        bd, usuario.id, MotivoCierre.CAMBIO_CONTRASENA, ahora, excepto_id=sesion.id
    )
    auditoria.registrar(
        bd,
        accion="sesion.cambio_contrasena",
        entidad=ENTIDAD,
        entidad_id=usuario.id,
        usuario_id=usuario.id,
        despues={"otras_sesiones_cerradas": cerradas},
        ip=ip,
    )
