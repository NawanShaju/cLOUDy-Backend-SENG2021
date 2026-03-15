import pytest
from unittest.mock import MagicMock
from app.services.db_services.xml_db import get_order_xml


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


def test_get_order_xml_not_found(mock_db):
    mock_db.execute_query.return_value = None

    result = get_order_xml(mock_db, "order1")

    assert result is None


def test_get_order_xml_memoryview(mock_db):
    xml_text = "<Order>test</Order>"
    mock_db.execute_query.return_value = [memoryview(xml_text.encode("utf-8"))]

    result = get_order_xml(mock_db, "order1")

    assert result == xml_text


def test_get_order_xml_bytes(mock_db):
    xml_text = "<Order>test</Order>"
    mock_db.execute_query.return_value = [xml_text.encode("utf-8")]

    result = get_order_xml(mock_db, "order1")

    assert result == xml_text


def test_get_order_xml_hex_string(mock_db):
    xml_text = "<Order>test</Order>"
    hex_text = "\\x" + xml_text.encode("utf-8").hex()

    mock_db.execute_query.return_value = [hex_text]

    result = get_order_xml(mock_db, "order1")

    assert result == xml_text


def test_get_order_xml_plain_string(mock_db):
    xml_text = "<Order>test</Order>"
    mock_db.execute_query.return_value = [xml_text]

    result = get_order_xml(mock_db, "order1")

    assert result == xml_text