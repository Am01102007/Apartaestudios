from datetime import timedelta

import pytest
from sqlalchemy import select

from app.comandos import purgar_sesiones
from app.core.tiempo import ahora_utc
from app.modulos.usuarios.modelos import Sesion
from tests.integration.ayudas import crear_usuario

pytestmark = pytest.mark.integracion


def _sesion(usuario_id: int, id_: str, *, creada_hace: int, cerrada: bool) -> Sesion:
    creada = ahora_utc() - timedelta(days=creada_hace)
    return Sesion(
        id=id_,
        usuario_id=usuario_id,
        hash_csrf="x" * 64,
        creada_en=creada,
        ultimo_uso=creada,
        expira_en=creada + timedelta(hours=12),
        cerrada_en=creada + timedelta(hours=1) if cerrada else None,
    )


def test_m8_purga_solo_las_sesiones_antiguas(sesion_bd, monkeypatch, capsys):
    usuario_id = crear_usuario(sesion_bd, "purga").id
    sesion_bd.add_all(
        [
            _sesion(usuario_id, "vieja-cerrada", creada_hace=100, cerrada=True),
            _sesion(usuario_id, "vieja-vencida", creada_hace=100, cerrada=False),
            _sesion(usuario_id, "reciente", creada_hace=10, cerrada=True),
        ]
    )
    sesion_bd.commit()
    monkeypatch.setattr(purgar_sesiones, "abrir_sesion", lambda: sesion_bd)

    assert purgar_sesiones.main(["--dias", "90"]) == 0
    restantes = sesion_bd.scalars(select(Sesion.id).where(Sesion.usuario_id == usuario_id)).all()
    assert restantes == ["reciente"]
    assert "Sesiones borradas: 2." in capsys.readouterr().out
