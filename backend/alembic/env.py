"""Entorno de migraciones de Alembic."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import obtener_configuracion
from app.db.modelos import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Las pruebas pasan su propia URL. En otro caso, las migraciones usan el rol dueño de las
# tablas (APP_DATABASE_URL_MIGRACIONES) y, si no está definido, el de la aplicación.
if not config.get_main_option("sqlalchemy.url"):
    configuracion = obtener_configuracion()
    url = configuracion.database_url_migraciones or configuracion.database_url
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))

target_metadata = Base.metadata


def ejecutar_sin_conexion() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def ejecutar_con_conexion() -> None:
    motor = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with motor.connect() as conexion:
        context.configure(connection=conexion, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    ejecutar_sin_conexion()
else:
    ejecutar_con_conexion()
