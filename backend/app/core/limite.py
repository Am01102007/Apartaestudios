"""Límite de peticiones en memoria, por clave (por ejemplo, la IP en el inicio de sesión).

Vive en la memoria del proceso: con varios procesos, cada uno cuenta por separado. Es
suficiente para el MVP; si se despliega con varios procesos, se moverá a la base de datos.
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock


class LimiteVentana:
    def __init__(self, maximo: int, ventana: timedelta):
        self.maximo = maximo
        self.ventana = ventana
        self._eventos: dict[str, deque[datetime]] = defaultdict(deque)
        self._candado = Lock()

    def permitir(self, clave: str, ahora: datetime) -> bool:
        with self._candado:
            eventos = self._eventos[clave]
            while eventos and eventos[0] <= ahora - self.ventana:
                eventos.popleft()
            if len(eventos) >= self.maximo:
                return False
            eventos.append(ahora)
            return True
