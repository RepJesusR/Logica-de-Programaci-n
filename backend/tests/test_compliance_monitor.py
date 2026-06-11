"""Tests unitarios para la lógica de compliance — sin dependencias externas."""
import pytest
from datetime import date, timedelta
from app.models.documento import EstadoDocumento
from app.services.compliance.monitor import _calcular_estado


def test_documento_vigente():
    fecha = date.today() + timedelta(days=30)
    estado, dias = _calcular_estado(fecha, dias_preaviso=15)
    assert estado == EstadoDocumento.VIGENTE
    assert dias == 30


def test_documento_por_vencer():
    fecha = date.today() + timedelta(days=10)
    estado, dias = _calcular_estado(fecha, dias_preaviso=15)
    assert estado == EstadoDocumento.POR_VENCER
    assert dias == 10


def test_documento_vencido():
    fecha = date.today() - timedelta(days=5)
    estado, dias = _calcular_estado(fecha, dias_preaviso=15)
    assert estado == EstadoDocumento.VENCIDO
    assert dias == -5


def test_documento_vence_hoy():
    fecha = date.today()
    estado, dias = _calcular_estado(fecha, dias_preaviso=15)
    assert estado == EstadoDocumento.POR_VENCER
    assert dias == 0


def test_sin_fecha():
    estado, dias = _calcular_estado(None, dias_preaviso=15)
    assert estado == EstadoDocumento.SIN_DOCUMENTO
    assert dias is None


def test_umbral_exacto():
    fecha = date.today() + timedelta(days=15)
    estado, dias = _calcular_estado(fecha, dias_preaviso=15)
    assert estado == EstadoDocumento.POR_VENCER
    assert dias == 15


def test_umbral_personalizado():
    fecha = date.today() + timedelta(days=8)
    estado_std, _ = _calcular_estado(fecha, dias_preaviso=15)
    estado_corto, _ = _calcular_estado(fecha, dias_preaviso=5)
    assert estado_std == EstadoDocumento.POR_VENCER
    assert estado_corto == EstadoDocumento.VIGENTE
