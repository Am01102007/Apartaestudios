"""RP-02 y RP-03: normalización de documentos y códigos, y validación de entradas."""

import pytest
from pydantic import ValidationError

from app.modulos.inmuebles.esquemas import (
    ApartaestudioCrear,
    ApartaestudioEditar,
    PropietarioCrear,
)
from app.modulos.inmuebles.reglas import normalizar_codigo, normalizar_documento, patron_busqueda


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("1.234.567", "1234567"), (" 900 123 456-7 ", "9001234567"), ("ab-12 3", "AB123")],
)
def test_normalizar_documento(entrada, esperado):
    assert normalizar_documento(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("  a-302 ", "A-302"), ("torre  b   2", "TORRE B 2"), ("201", "201")],
)
def test_normalizar_codigo(entrada, esperado):
    assert normalizar_codigo(entrada) == esperado


def test_patron_busqueda_trata_comodines_como_texto():
    assert patron_busqueda("50%_a") == "%50\\%\\_a%"


def _propietario(**cambios):
    return {"nombre": "Ana Ruiz", "tipo_documento": "CC", "numero_documento": "1.234.567"} | cambios


def test_propietario_normaliza_el_documento():
    assert PropietarioCrear(**_propietario()).numero_documento == "1234567"


@pytest.mark.parametrize(
    "cambios",
    [
        {"numero_documento": "12"},  # muy corto
        {"numero_documento": "123456789012345678901"},  # muy largo
        {"numero_documento": "12#45"},
        {"tipo_documento": "CC", "numero_documento": "AB1234"},  # CC solo dígitos
        {"tipo_documento": "XX"},
        {"nombre": "   "},
        {"telefono": "abc"},
        {"correo": "sin-arroba"},
        {"ocupacion": "ocupado"},  # campo desconocido
    ],
)
def test_propietario_rechaza_datos_invalidos(cambios):
    with pytest.raises(ValidationError):
        PropietarioCrear(**_propietario(**cambios))


def test_pasaporte_admite_letras():
    datos = PropietarioCrear(**_propietario(tipo_documento="PA", numero_documento="ab-123456"))
    assert datos.numero_documento == "AB123456"


def _apartaestudio(**cambios):
    return {"codigo": " a-302 ", "propietario_id": 1, "direccion": "Calle 10 # 5-20"} | cambios


def test_apartaestudio_normaliza_el_codigo():
    assert ApartaestudioCrear(**_apartaestudio()).codigo == "A-302"


@pytest.mark.parametrize(
    "cambios",
    [
        {"codigo": ""},
        {"codigo": "-302"},  # debe empezar con letra o número
        {"codigo": "A/302"},
        {"codigo": "X" * 21},
        {"area_m2": "0"},
        {"area_m2": "12.345"},
        {"ocupacion": "ocupado"},  # P-06: la ocupación no se envía
        {"en_mantenimiento": True},  # se cambia solo por su endpoint
        {"activo": False},
    ],
)
def test_apartaestudio_rechaza_datos_invalidos(cambios):
    with pytest.raises(ValidationError):
        ApartaestudioCrear(**_apartaestudio(**cambios))


def test_editar_no_admite_nulos_en_campos_obligatorios():
    with pytest.raises(ValidationError):
        ApartaestudioEditar(codigo=None)
    assert ApartaestudioEditar(area_m2=None).model_fields_set == {"area_m2"}
