"""Tipos y base comunes de los esquemas de entrada (Pydantic)."""

from typing import Annotated, Any, ClassVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, StringConstraints, model_validator

from app.core.documentos import normalizar_documento


def si_es_texto(funcion):
    """Aplica `funcion` antes de validar, solo si el valor es texto."""
    return BeforeValidator(lambda valor: funcion(valor) if isinstance(valor, str) else valor)


def texto(minimo: int, maximo: int):
    return Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=minimo, max_length=maximo)
    ]


# Se normaliza antes de validar el formato.
NumeroDocumento = Annotated[
    str, si_es_texto(normalizar_documento), StringConstraints(pattern=r"^[A-Z0-9]{3,20}$")
]
Telefono = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9 ()-]{7,20}$")]
Correo = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_lower=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    ),
]


class Entrada(BaseModel):
    """Rechaza campos desconocidos. En las ediciones, omitir un campo lo deja igual y enviarlo
    nulo solo vale si es opcional: los obligatorios se listan en `obligatorios`."""

    model_config = ConfigDict(extra="forbid")

    obligatorios: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def _sin_nulos_obligatorios(self) -> Any:
        for campo in self.obligatorios:
            if campo in self.model_fields_set and getattr(self, campo) is None:
                raise ValueError(f"{campo} no puede ser nulo")
        return self
