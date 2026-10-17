"""Límite de peticiones en memoria, por clave (por ejemplo, la IP en el inicio de sesión).

Vive en la memoria del proceso: con varios procesos, cada uno cuenta por separado. Es
suficiente para el MVP; si se despliega con varios procesos, se moverá a la base de datos.
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from threading import Lock

# Cuando hay más claves que esto, se eliminan las que no tienen intentos recientes.
MAXIMO_CLAVES_ANTES_DE_LIMPIAR = 1000


class LimiteVentana:
    def __init__(self, maximo: int, ventana: timedelta):
        self.maximo = maximo
        self.ventana = ventana
        self._eventos: dict[str, deque[datetime]] = defaultdict(deque)
        self._candado = Lock()

    def permitir(self, clave: str, ahora: datetime) -> bool:
        limite_antiguedad = ahora - self.ventana
        with self._candado:
            if len(self._eventos) > MAXIMO_CLAVES_ANTES_DE_LIMPIAR:
                self._olvidar_inactivas(limite_antiguedad)
            eventos = self._eventos[clave]
            while eventos and eventos[0] <= limite_antiguedad:
                eventos.popleft()
            if len(eventos) >= self.maximo:
                return False
            eventos.append(ahora)
            return True

    @property
    def claves(self) -> int:
        return len(self._eventos)

    def _olvidar_inactivas(self, limite_antiguedad: datetime) -> None:
        inactivas = [c for c, e in self._eventos.items() if not e or e[-1] <= limite_antiguedad]
        for clave in inactivas:
            del self._eventos[clave]
