from sqlalchemy.exc import OperationalError

from app.db.sesion import obtener_sesion


class SesionCaida:
    def execute(self, *_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("sin conexión"))


def test_salud_informa_degradado_si_no_hay_base_de_datos(app, cliente):
    app.dependency_overrides[obtener_sesion] = lambda: SesionCaida()
    r = cliente.get("/api/v1/salud")
    assert r.status_code == 503
    assert r.json() == {"estado": "degradado", "base_de_datos": "sin_conexion"}


def test_health_live_no_depende_de_la_base(app, cliente):
    app.dependency_overrides[obtener_sesion] = lambda: SesionCaida()
    r = cliente.get("/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}


def test_health_ready_falla_si_no_hay_base_de_datos(app, cliente):
    app.dependency_overrides[obtener_sesion] = lambda: SesionCaida()
    r = cliente.get("/health/ready")
    assert r.status_code == 503
    assert r.json() == {"database": "unavailable"}
