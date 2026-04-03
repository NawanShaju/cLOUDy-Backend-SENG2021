import pytest
from unittest.mock import MagicMock
from app.services.db_services.order_db import cancel_order
from app.services.order_service import cancel_order_service

@pytest.fixture
def mock_db():
    db = MagicMock()
    return db

def test_cancel_order_not_found(mock_db):
    mock_db.execute_query.return_value = None

    result = cancel_order_service(mock_db, "buyer1", "order1")

    assert result["status"] == 404
    assert result["error"] == "Order not found"


def test_cancel_order_wrong_buyer(mock_db):
    mock_db.execute_query.return_value = [
        ("order1", "other-buyer", None, None, None, None, "CREATED", None, None, None)
    ]

    result = cancel_order_service(mock_db, "buyer1", "order1")

    assert result["status"] == 403
    assert "Forbidden" in result["error"]


def test_cancel_order_invalid(mock_db):
    mock_db.execute_query.return_value = [
        ("order1", "buyer1", None, None, None, None, "CANCELED")
    ]

    result = cancel_order_service(mock_db, "buyer1", "order1")

    assert result["status"] == 409
    assert "cannot be canceled" in result["error"]


def test_cancel_order(mock_db):
    mock_db.execute_query.return_value = [
        ("order1", "buyer1", None, None, None, None, "CREATED")
    ]

    result = cancel_order_service(mock_db, "buyer1", "order1")

    mock_db.execute_insert_update_delete.assert_called_once()

    assert result["status"] == "CANCELED"
    assert result["orderId"] == "order1"


def test_cancel_order(mock_db):
    cancel_order(mock_db, "order1")

    mock_db.execute_insert_update_delete.assert_called_once()

    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["order_id"] == "order1"


def test_cancel_order_service(mock_db):
    mock_db.execute_query.return_value = [
        ("order1", "buyer1", None, None, None, None, "CREATED")
    ]

    result = cancel_order_service(mock_db, "buyer1", "order1")

    assert result["status"] == "CANCELED"