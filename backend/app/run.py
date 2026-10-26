"""Arranque de la API en contenedor: escucha en 0.0.0.0 y en el puerto de $PORT (Railway).

Uso:  python -m app.run
"""

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # noqa: S104 - dentro del contenedor; el hosting controla la exposición
        port=int(os.environ.get("PORT", "8000")),
        # Detrás del proxy del hosting, para que el límite de ingresos use la IP real.
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
