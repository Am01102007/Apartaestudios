from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, ConId, ConMarcasDeTiempo


class Rol(StrEnum):
    ADMINISTRADOR = "administrador"
    EMPLEADO = "empleado"


class MotivoCierre(StrEnum):
    LOGOUT = "logout"
    INACTIVIDAD = "inactividad"
    DESACTIVADO = "desactivado"
    CAMBIO_CONTRASENA = "cambio_contrasena"
    CAMBIO_ROL = "cambio_rol"
    RESTABLECIMIENTO = "restablecimiento"


def _texto_enumerado(enumeracion: type[StrEnum], longitud: int) -> Enum:
    """Guarda el valor como VARCHAR (la restricción CHECK se declara aparte, con nombre)."""
    return Enum(
        enumeracion,
        native_enum=False,
        create_constraint=False,
        length=longitud,
        values_callable=lambda miembros: [m.value for m in miembros],
    )


class Usuario(ConId, ConMarcasDeTiempo, Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint("rol IN ('administrador', 'empleado')", name="rol_valido"),
        CheckConstraint("nombre_usuario = lower(nombre_usuario)", name="nombre_usuario_minusculas"),
        CheckConstraint("intentos_fallidos >= 0", name="intentos_no_negativos"),
    )

    nombre_usuario: Mapped[str] = mapped_column(String(30), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str | None] = mapped_column(String(254))
    hash_contrasena: Mapped[str] = mapped_column(String(255))
    rol: Mapped[Rol] = mapped_column(_texto_enumerado(Rol, 20))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), default=True)
    debe_cambiar_contrasena: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), default=False
    )
    intentos_fallidos: Mapped[int] = mapped_column(
        SmallInteger, server_default=text("0"), default=0
    )
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_ingreso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def es_administrador(self) -> bool:
        return self.rol == Rol.ADMINISTRADOR


class Sesion(Base):
    """Sesión abierta en el servidor. El JWT de la cookie solo lleva su identificador."""

    __tablename__ = "sesiones"
    __table_args__ = (
        CheckConstraint(
            "motivo_cierre IN ('logout', 'inactividad', 'desactivado', 'cambio_contrasena', "
            "'cambio_rol', 'restablecimiento')",
            name="motivo_cierre_valido",
        ),
        Index(
            "ix_sesiones_usuario_abiertas",
            "usuario_id",
            postgresql_where=text("cerrada_en IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuarios.id"))
    hash_csrf: Mapped[str] = mapped_column(String(64))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ultimo_uso: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cerrada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo_cierre: Mapped[MotivoCierre | None] = mapped_column(_texto_enumerado(MotivoCierre, 30))
    ip: Mapped[str | None] = mapped_column(String(45))
    agente_usuario: Mapped[str | None] = mapped_column(String(255))

    usuario: Mapped[Usuario] = relationship(lazy="joined")
