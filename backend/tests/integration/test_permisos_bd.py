"""I4: el rol de la aplicación no es dueño de las tablas y no puede alterar la auditoría.

Solo se ejecuta si el rol existe en el servidor (se crea con scripts/roles.sql).
"""

import pytest
from sqlalchemy import text

from app.core.config import obtener_configuracion

pytestmark = pytest.mark.integracion
ROL = obtener_configuracion().rol_aplicacion


@pytest.fixture
def privilegio(sesion_bd):
    if not sesion_bd.execute(
        text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": ROL}
    ).scalar():
        pytest.skip(f"El rol {ROL} no existe en este servidor (ver scripts/roles.sql)")

    def consultar(tabla: str, permiso: str) -> bool:
        return sesion_bd.execute(
            text("SELECT has_table_privilege(:r, :t, :p)"), {"r": ROL, "t": tabla, "p": permiso}
        ).scalar()

    return consultar


@pytest.mark.parametrize(
    ("tabla", "permiso", "esperado"),
    [
        ("auditoria", "INSERT", True),
        ("auditoria", "SELECT", True),
        ("auditoria", "UPDATE", False),
        ("auditoria", "DELETE", False),
        ("auditoria", "TRUNCATE", False),
        ("usuarios", "UPDATE", True),
        ("usuarios", "DELETE", False),
        ("sesiones", "DELETE", True),
        ("bloqueos", "UPDATE", True),
        ("bloqueos", "DELETE", False),
        ("bloqueos", "TRUNCATE", False),
        ("residentes", "DELETE", False),
        ("propietarios", "DELETE", False),
        ("apartaestudios", "DELETE", False),
        ("contratos", "UPDATE", True),
        ("contratos", "DELETE", False),
        ("contratos", "TRUNCATE", False),
        ("prorrogas", "INSERT", True),
        ("prorrogas", "DELETE", False),
        ("alembic_version", "SELECT", False),
    ],
)
def test_permisos_del_rol_de_la_aplicacion(privilegio, tabla, permiso, esperado):
    assert privilegio(tabla, permiso) is esperado


def test_el_rol_de_la_aplicacion_no_es_dueno_de_ninguna_tabla(sesion_bd, privilegio):
    duenos = (
        sesion_bd.execute(
            text("SELECT DISTINCT tableowner FROM pg_tables WHERE schemaname = 'public'")
        )
        .scalars()
        .all()
    )
    assert ROL not in duenos
