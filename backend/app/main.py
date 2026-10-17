"""Punto de entrada de la API.

Ejecutar en desarrollo:  uvicorn app.main:app --reload
"""

import logging
from datetime import timedelta

from fastapi import FastAPI

from app.api.router import api_v1
from app.core.config import Configuracion, obtener_configuracion
from app.core.errores import registrar_manejadores
from app.core.limite import LimiteVentana
from app.core.seguridad_http import CabecerasSeguridad


def crear_app(configuracion: Configuracion | None = None) -> FastAPI:
    configuracion = configuracion or obtener_configuracion()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    docs = configuracion.docs_habilitadas and not configuracion.es_produccion

    app = FastAPI(
        title="API de administración de apartaestudios",
        version="0.1.0",
        description="API REST del MVP. Montos en pesos colombianos; fechas en hora de Bogotá.",
        docs_url="/api/docs" if docs else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if docs else None,
    )
    app.state.configuracion = configuracion
    app.state.limite_ingreso = LimiteVentana(
        configuracion.ingresos_por_minuto_por_ip, timedelta(minutes=1)
    )
    app.add_middleware(CabecerasSeguridad)
    registrar_manejadores(app)
    app.include_router(api_v1)
    return app


app = crear_app()
