import pytest
from unittest.mock import MagicMock
from app.services.xml_db import xml_to_db_update_cancel

@pytest.fixture
def mock_db():
    return MagicMock()

def test_xml_to_db_update_cancel_plain_string(mock_db):
    order_id = "order123"
    xml = "<order><status>cancelled</status></order>"

    xml_to_db_update_cancel(mock_db, xml, order_id)

    mock_db.execute_insert_update_delete.assert_called_once()
    _, params = mock_db.execute_insert_update_delete.call_args[0]
    assert params["xml_content"] == xml
    assert params["order_id"] == order_id

def test_xml_to_db_update_cancel_bytes(mock_db):
    order_id = "order123"
    xml = b"<order><status>cancelled</status></order>"

    xml_to_db_update_cancel(mock_db, xml, order_id)

    _, params = mock_db.execute_insert_update_delete.call_args[0]
    assert params["xml_content"] == xml
    assert params["order_id"] == order_id
    