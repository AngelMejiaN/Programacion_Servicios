"""
Pruebas unitarias para backend/services/programacion.py.
No requieren base de datos — toda la lógica es pura o usa mocks.

Ejecutar desde la raíz del proyecto:
    python -m pytest backend/tests/ -v
"""
import pytest
from datetime import date, time
from unittest.mock import MagicMock

from fastapi import HTTPException

from backend.services.programacion import (
    calcular_hora_llegada,
    calcular_hora_retorno,
    validar_y_enriquecer,
)
from backend.schemas.servicio import ServicioCreate


# ── calcular_hora_llegada ─────────────────────────────────────────────────────

def test_hora_llegada_mismo_dia():
    hora, cruza = calcular_hora_llegada(time(8, 0), 90)
    assert hora == time(9, 30)
    assert not cruza


def test_hora_llegada_cruza_medianoche():
    hora, cruza = calcular_hora_llegada(time(23, 0), 90)
    assert hora == time(0, 30)
    assert cruza


def test_hora_llegada_exactamente_medianoche():
    hora, cruza = calcular_hora_llegada(time(22, 0), 120)
    assert hora == time(0, 0)
    assert cruza


def test_hora_llegada_justo_antes_medianoche():
    hora, cruza = calcular_hora_llegada(time(22, 0), 119)
    assert hora == time(23, 59)
    assert not cruza


def test_hora_llegada_minuto_cero():
    hora, cruza = calcular_hora_llegada(time(6, 30), 0)
    assert hora == time(6, 30)
    assert not cruza


# ── calcular_hora_retorno ─────────────────────────────────────────────────────

def test_retorno_sin_tiempo_estimado():
    hora, fecha = calcular_hora_retorno(time(14, 0), None, date(2026, 6, 20))
    assert hora is None
    assert fecha is None


def test_retorno_mismo_dia():
    hora, fecha = calcular_hora_retorno(time(14, 0), 60, date(2026, 6, 20))
    assert hora == time(15, 0)
    assert fecha is None


def test_retorno_cruza_dia():
    hora, fecha = calcular_hora_retorno(time(23, 30), 60, date(2026, 6, 20))
    assert hora == time(0, 30)
    assert fecha == date(2026, 6, 21)


# ── validar_y_enriquecer — Tipo A ─────────────────────────────────────────────

def _make_data(**kwargs):
    defaults = dict(
        fecha=date(2026, 6, 20), ruta_id=1, sede_id=1,
        vehiculo_id=1, conductor_id=1, hora_inicio=time(8, 0),
    )
    defaults.update(kwargs)
    return ServicioCreate(**defaults)


def _ruta_tipo_a(calcula=True, tiempo=90, dos_cond=False):
    r = MagicMock()
    r.sede.tipo = "A"
    r.calcula_llegada = calcula
    r.tiempo_estimado_min = tiempo
    r.origen_fijo = True
    r.requiere_dos_conductores = dos_cond
    return r


def test_tipo_a_calcula_hora_llegada():
    extras = validar_y_enriquecer(_make_data(), _ruta_tipo_a(), MagicMock())
    assert extras["hora_llegada_est"] == time(9, 30)
    assert "fecha_llegada" not in extras


def test_tipo_a_calcula_llegada_cruza_medianoche():
    data = _make_data(hora_inicio=time(23, 0))
    extras = validar_y_enriquecer(data, _ruta_tipo_a(tiempo=90), MagicMock())
    assert extras["hora_llegada_est"] == time(0, 30)
    assert extras["fecha_llegada"] == date(2026, 6, 21)


def test_tipo_a_sin_calculo_no_enriquece():
    extras = validar_y_enriquecer(_make_data(), _ruta_tipo_a(calcula=False), MagicMock())
    assert "hora_llegada_est" not in extras


# ── validar_y_enriquecer — Tipo B ─────────────────────────────────────────────

def _ruta_tipo_b_variable():
    r = MagicMock()
    r.sede.tipo = "B"
    r.origen_fijo = False
    r.requiere_dos_conductores = False
    return r


def test_tipo_b_variable_sin_paradero_lanza_422():
    with pytest.raises(HTTPException) as exc:
        validar_y_enriquecer(_make_data(paradero_origen_id=None),
                              _ruta_tipo_b_variable(), MagicMock())
    assert exc.value.status_code == 422


def test_tipo_b_variable_paradero_no_pertenece_a_ruta_lanza_422():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None  # no existe
    with pytest.raises(HTTPException) as exc:
        validar_y_enriquecer(_make_data(paradero_origen_id=99),
                              _ruta_tipo_b_variable(), db)
    assert exc.value.status_code == 422


def test_tipo_b_variable_paradero_valido_no_lanza():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock()  # existe
    extras = validar_y_enriquecer(_make_data(paradero_origen_id=5),
                                   _ruta_tipo_b_variable(), db)
    assert extras == {}


def test_tipo_b_fija_no_exige_paradero():
    r = MagicMock()
    r.sede.tipo = "B"
    r.origen_fijo = True
    r.requiere_dos_conductores = False
    extras = validar_y_enriquecer(_make_data(), r, MagicMock())
    assert extras == {}


# ── validar_y_enriquecer — Rutas de mina ─────────────────────────────────────

def test_mina_sin_segundo_conductor_lanza_422():
    ruta = _ruta_tipo_a(dos_cond=True)
    with pytest.raises(HTTPException) as exc:
        validar_y_enriquecer(_make_data(conductor2_id=None), ruta, MagicMock())
    assert exc.value.status_code == 422


def test_mina_con_segundo_conductor_ok():
    ruta = _ruta_tipo_a(dos_cond=True)
    extras = validar_y_enriquecer(_make_data(conductor2_id=2), ruta, MagicMock())
    assert "hora_llegada_est" in extras  # calcula_llegada=True, tiempo=90
