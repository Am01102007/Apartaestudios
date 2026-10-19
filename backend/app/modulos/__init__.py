"""Dominios funcionales del sistema.

Cada dominio vive en su propia carpeta con estas capas:

    router.py       HTTP: rutas, permisos y códigos de estado; confirma la transacción
    esquemas.py     Esquemas Pydantic de entrada y salida
    servicio.py     Casos de uso y reglas de negocio; nunca confirma (solo flush)
    reglas.py       (opcional) Cálculos puros, probados sin base de datos
    repositorio.py  Consultas a la base de datos
    modelos.py      Tablas SQLAlchemy

Dependencias permitidas: router -> servicio -> repositorio -> modelos.
Un servicio puede usar el servicio de otro dominio, nunca su repositorio.
"""
