"""Configuración de la aplicación, leída de variables de entorno con prefijo APP_.

Los secretos (cadena de conexión, clave de firma) solo llegan por entorno o por el archivo
.env, que no se versiona.
"""

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Solo sirve para desarrollo y pruebas; en producción la API no arranca con ella.
CLAVE_JWT_DESARROLLO = "clave-de-desarrollo-no-usar-en-produccion-0123456789"


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    entorno: Literal["desarrollo", "pruebas", "produccion"] = "desarrollo"
    database_url: str = (
        "postgresql+psycopg://apartaestudios:apartaestudios@localhost:5432/apartaestudios"
    )
    database_url_pruebas: str = (
        "postgresql+psycopg://apartaestudios:apartaestudios@localhost:5432/apartaestudios_test"
    )
    docs_habilitadas: bool = True
    zona_horaria: str = "America/Bogota"

    # Sesión (decisiones D-3 y fase 6)
    clave_jwt: str = CLAVE_JWT_DESARROLLO
    cookie_segura: bool = True
    minutos_inactividad: int = 30
    horas_maximas_sesion: int = 12
    intentos_fallidos_maximos: int = 5
    minutos_bloqueo: int = 15
    ingresos_por_minuto_por_ip: int = 20

    @property
    def es_produccion(self) -> bool:
        return self.entorno == "produccion"

    @model_validator(mode="after")
    def _validar_produccion(self) -> "Configuracion":
        if len(self.clave_jwt) < 32:
            raise ValueError("APP_CLAVE_JWT debe tener al menos 32 caracteres")
        if self.es_produccion:
            if self.clave_jwt == CLAVE_JWT_DESARROLLO:
                raise ValueError("APP_CLAVE_JWT debe definirse en producción")
            if not self.cookie_segura:
                raise ValueError("APP_COOKIE_SEGURA no puede desactivarse en producción")
        return self


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
