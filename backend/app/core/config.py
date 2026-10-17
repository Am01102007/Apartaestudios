"""Configuración de la aplicación, leída de variables de entorno con prefijo APP_.

Los secretos (cadena de conexión, claves) solo llegan por entorno o por el archivo .env,
que no se versiona.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def es_produccion(self) -> bool:
        return self.entorno == "produccion"


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
