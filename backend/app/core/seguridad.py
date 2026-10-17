"""Primitivas de seguridad: hash de contraseñas, tokens aleatorios y JWT.

No contiene reglas de negocio; la sesión y los permisos están en app.modulos.usuarios.
"""

import hashlib
import hmac
import secrets
from datetime import datetime

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

ALGORITMO_JWT = "HS256"
_hasher = PasswordHasher()  # Argon2id con los parámetros recomendados por la librería

# Hash de una contraseña que nadie conoce. Se verifica contra él cuando el usuario no existe,
# para que el tiempo de respuesta no revele qué nombres de usuario están registrados.
_HASH_FICTICIO = _hasher.hash(secrets.token_urlsafe(32))


def hashear_contrasena(contrasena: str) -> str:
    return _hasher.hash(contrasena)


def verificar_contrasena(hash_guardado: str | None, contrasena: str) -> bool:
    try:
        return _hasher.verify(hash_guardado or _HASH_FICTICIO, contrasena)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def requiere_rehash(hash_guardado: str) -> bool:
    return _hasher.check_needs_rehash(hash_guardado)


def generar_token() -> str:
    """Token aleatorio de 256 bits, apto para URL y cookies."""
    return secrets.token_urlsafe(32)


def resumen_token(token: str) -> str:
    """SHA-256 de un token, para guardarlo sin poder reconstruirlo."""
    return hashlib.sha256(token.encode()).hexdigest()


def tokens_iguales(token: str, resumen_guardado: str) -> bool:
    return hmac.compare_digest(resumen_token(token), resumen_guardado)


def crear_jwt(
    clave: str, id_sesion: str, usuario_id: int, emitido: datetime, expira: datetime
) -> str:
    datos = {"sub": str(usuario_id), "sid": id_sesion, "iat": emitido, "exp": expira}
    return jwt.encode(datos, clave, algorithm=ALGORITMO_JWT)


def leer_jwt(clave: str, token: str, ahora: datetime) -> dict | None:
    """Devuelve los datos del token si la firma es válida y no ha vencido; si no, None."""
    try:
        datos = jwt.decode(
            token,
            clave,
            algorithms=[ALGORITMO_JWT],
            options={
                "require": ["sub", "sid", "exp", "iat"],
                "verify_exp": False,
                "verify_iat": False,
            },
        )
    except jwt.PyJWTError:
        return None
    # Las fechas se comparan con el reloj de la aplicación, para poder probarlas.
    if datos["exp"] <= ahora.timestamp():
        return None
    return datos
