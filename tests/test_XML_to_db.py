import pytest
from unittest.mock import MagicMock
from app.services.xml_db import xml_to_db

@pytest.fixture
def mock_db():
    return MagicMock()

def test_xml_to_db_calls_db(mock_db):
    xml_to_db(mock_db, "<order/>", "order-001")
    mock_db.execute_insert_update_delete.assert_called_once()

def test_xml_to_db_passes_correct_params(mock_db):
    xml_to_db(mock_db, "<order/>", "order-001")
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["order_id"] == "order-001"
    assert params["xml_content"] == "<order/>"
    assert params["document_version"] == 1