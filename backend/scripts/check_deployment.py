"""Comprueba una API desplegada: /health/live y /health/ready durante hasta 5 minutos.

Uso:  python scripts/check_deployment.py https://<servicio>.up.railway.app
"""

import json
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

base_url = sys.argv[1].rstrip("/")
deadline = time.monotonic() + 300

while time.monotonic() < deadline:
    try:
        with urlopen(f"{base_url}/health/live", timeout=10) as response:  # noqa: S310
            if response.status != 200:
                raise RuntimeError(f"live: HTTP {response.status}")

        with urlopen(f"{base_url}/health/ready", timeout=10) as response:  # noqa: S310
            data = json.load(response)
            if response.status == 200 and data.get("database") == "ready":
                print("API y PostgreSQL listos")
                sys.exit(0)
            raise RuntimeError(f"ready: {data}")

    except (OSError, URLError, ValueError, RuntimeError) as error:
        print(f"Esperando API: {error}")
        time.sleep(5)

sys.exit("La API no quedó lista en 5 minutos")
