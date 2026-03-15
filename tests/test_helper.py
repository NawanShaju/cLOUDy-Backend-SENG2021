import pytest
from datetime import datetime
from app.utils.helper import to_iso_date, is_valid_uuid

def test_to_iso_date_with_datetime_object():
    dt = datetime(2024, 1, 15, 10, 30, 0)
    result = to_iso_date(dt)
    assert result == "2024-01-15T10:30:00"

def test_to_iso_date_with_valid_string():
    result = to_iso_date("2024-01-15")
    assert result is not None

def test_to_iso_date_with_invalid_string():
    with pytest.raises(ValueError):
        to_iso_date("not-a-date")

def test_to_iso_date_with_invalid_type():
    with pytest.raises(TypeError):
        to_iso_date(12345)

def test_is_valid_uuid_with_valid_uuid():
    result = is_valid_uuid("f5b163a5-b189-4666-8666-9527705b6ce9")
    assert result is True

def test_is_valid_uuid_with_invalid_uuid():
    result = is_valid_uuid("not-a-uuid")
    assert result is False

def test_is_valid_uuid_with_empty_string():
    result = is_valid_uuid("")
    assert result is False
    