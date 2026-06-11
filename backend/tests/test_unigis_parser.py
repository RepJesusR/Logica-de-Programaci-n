"""Tests del parser de respuestas UNIGIS — usa objetos mock sin conexión SOAP real."""
import pytest
from datetime import date
from unittest.mock import MagicMock
from app.services.unigis.documentos import _parse_fecha, _parse_documento


def test_parse_fecha_iso():
    assert _parse_fecha("2025-03-15") == date(2025, 3, 15)


def test_parse_fecha_datetime_str():
    assert _parse_fecha("2025-03-15T00:00:00") == date(2025, 3, 15)


def test_parse_fecha_none():
    assert _parse_fecha(None) is None


def test_parse_fecha_date_obj():
    d = date(2025, 6, 1)
    assert _parse_fecha(d) == d


def test_parse_documento_completo():
    mock = MagicMock()
    mock.IdDocumento = 42
    mock.IdTipoDocumento = 7
    mock.TipoDocumento = "Licencia de conducir"
    mock.FechaVencimiento = "2026-01-31"
    mock.DiasPreavisoVencimiento = 30
    mock.NotificarMobile = True

    doc = _parse_documento(mock)
    assert doc.documento_id == 42
    assert doc.tipo_documento_id == 7
    assert doc.tipo_documento_nombre == "Licencia de conducir"
    assert doc.fecha_vencimiento == date(2026, 1, 31)
    assert doc.dias_preaviso == 30
    assert doc.notificar_mobile is True


def test_parse_documento_sin_fecha():
    mock = MagicMock()
    mock.IdDocumento = None
    mock.IdTipoDocumento = 3
    mock.TipoDocumento = "Seguro"
    mock.FechaVencimiento = None
    mock.DiasPreavisoVencimiento = None
    mock.NotificarMobile = False

    doc = _parse_documento(mock)
    assert doc.fecha_vencimiento is None
    assert doc.dias_preaviso == 15  # fallback default
