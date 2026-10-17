from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modulos.usuarios.modelos import Rol

# RU-01: letras sin tilde, números, punto, guion y guion bajo; se guarda en minúsculas.
NombreUsuario = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        to_lower=True,
        min_length=3,
        max_length=30,
        pattern=r"^[A-Za-z0-9._-]+$",
    ),
]
# RU-06: entre 10 y 128 caracteres.
Contrasena = Annotated[str, Field(min_length=10, max_length=128)]
Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Correo = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_lower=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    ),
]


class Entrada(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UsuarioCrear(Entrada):
    nombre_usuario: NombreUsuario
    nombre: Nombre
    correo: Correo | None = None
    rol: Rol
    contrasena_temporal: Contrasena


class UsuarioEditar(Entrada):
    nombre_usuario: NombreUsuario | None = None
    nombre: Nombre | None = None
    correo: Correo | None = None
    rol: Rol | None = None

    @model_validator(mode="after")
    def _sin_nulos_obligatorios(self) -> "UsuarioEditar":
        for campo in ("nombre_usuario", "nombre", "rol"):
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"{campo} no puede ser nulo")
        return self


class RestablecerContrasena(Entrada):
    contrasena_temporal: Contrasena


class UsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_usuario: str
    nombre: str
    correo: str | None
    rol: Rol
    activo: bool
    debe_cambiar_contrasena: bool
    bloqueado_hasta: datetime | None
    ultimo_ingreso: datetime | None
    creado_en: datetime


class CredencialesIngreso(Entrada):
    # Sin reglas de formato: un error de formato revelaría la política de contraseñas.
    nombre_usuario: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    contrasena: Annotated[str, StringConstraints(min_length=1, max_length=128)]


class CambioContrasena(Entrada):
    contrasena_actual: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    contrasena_nueva: Contrasena


class UsuarioActual(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre_usuario: str
    nombre: str
    rol: Rol
    debe_cambiar_contrasena: bool
