import pytest
from unittest.mock import MagicMock
from app.services.db_services.order_db import (
    delete_order_documents,
    delete_order_items,
    delete_order
)
from app.services.order_service import delete_order_service


@pytest.fixture
def mock_db():
    return MagicMock()


def test_delete_order_not_found(mock_db):
    mock_db.execute_query.return_value = None

    result = delete_order_service(mock_db, "buyer1", "order1")

    assert result["status"] == 404
    assert result["error"] == "Order not found"


def test_delete_order_forbidden(mock_db):
    mock_db.execute_query.return_value = (
        "order1",      # order_id
        "other_buyer", # buyer_id
        "x",
        "x",
        "x",
        "x",
        "CANCELED"     # status
    )

    result = delete_order_service(mock_db, "buyer1", "order1")

    assert result["status"] == 403
    assert "Forbidden" in result["error"]


def test_delete_order_not_canceled(mock_db):
    mock_db.execute_query.return_value = (
        "order1",
        "buyer1",
        "x",
        "x",
        "x",
        "x",
        "CREATED"
    )

    result = delete_order_service(mock_db, "buyer1", "order1")

    assert result["status"] == 409
    assert result["error"] == "Order cannot be deleted unless status is CANCELED"


def test_delete_order_success(mock_db):
    mock_db.execute_query.return_value = (
        "order1",
        "buyer1",
        "x",
        "x",
        "x",
        "x",
        "CANCELED"
    )

    result = delete_order_service(mock_db, "buyer1", "order1")

    assert mock_db.execute_insert_update_delete.call_count == 3
    assert result["orderId"] == "order1"
    assert result["message"] == "Order deleted successfully"


def test_delete_order_documents(mock_db):
    delete_order_documents(mock_db, "order1")

    mock_db.execute_insert_update_delete.assert_called_once()
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["order_id"] == "order1"


def test_delete_order_items(mock_db):
    delete_order_items(mock_db, "order1")

    mock_db.execute_insert_update_delete.assert_called_once()
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["order_id"] == "order1"


def test_delete_order(mock_db):
    delete_order(mock_db, "order1")

    mock_db.execute_insert_update_delete.assert_called_once()
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["order_id"] == "order1"