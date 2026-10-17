"""Borra las sesiones cerradas o vencidas hace más de N días (por defecto, 90).

Uso:
    uv run python -m app.comandos.purgar_sesiones [--dias 90]

Las sesiones ya no sirven para entrar; solo ocupan espacio. Los ingresos y cierres siguen
registrados en la auditoría, que no se borra. Conviene programarlo una vez al día o a la semana.
"""

import argparse
from datetime import timedelta

from app.comandos import abrir_sesion
from app.core.config import obtener_configuracion
from app.core.tiempo import ahora_utc
from app.modulos.usuarios import repositorio


def main(argumentos: list[str] | None = None) -> int:
    lector = argparse.ArgumentParser(description="Borra sesiones antiguas.")
    lector.add_argument(
        "--dias",
        type=int,
        default=obtener_configuracion().dias_retencion_sesiones,
        help="Antigüedad mínima en días (mínimo 1)",
    )
    opciones = lector.parse_args(argumentos)
    if opciones.dias < 1:
        lector.error("--dias debe ser al menos 1")

    with abrir_sesion() as sesion:
        borradas = repositorio.purgar_sesiones(sesion, ahora_utc() - timedelta(days=opciones.dias))
        sesion.commit()
    print(f"Sesiones borradas: {borradas}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
