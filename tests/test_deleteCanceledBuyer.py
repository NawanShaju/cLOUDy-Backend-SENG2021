import pytest
from unittest.mock import MagicMock
from app.services.orderdb import (
    delete_order_documents,
    delete_order_items,
    delete_order_input
)
from app.services.order_service import delete_buyers_all_cancelled_orders_service

@pytest.fixture
def mock_db():
    return MagicMock()


def test_delete_cancelled_orders_invalid(mock_db):
    mock_db.execute_query.return_value = None

    result = delete_buyers_all_cancelled_orders_service(mock_db, "buyer1")

    assert result["status"] == 404
    assert result["error"] == "Buyer not found"


def test_delete_cancelled_orders_none(mock_db):
    mock_db.execute_query.side_effect = [
        [("something",)], 
        []           
    ]

    result = delete_buyers_all_cancelled_orders_service(mock_db, "buyer1")

    assert result["status"] == 409
    assert "No canceled orders" in result["error"]


def test_delete_cancelled_orders(mock_db):
    mock_db.execute_query.side_effect = [
        [("something",)], 
        [("order1",), ("order2",)] 
    ]

    result = delete_buyers_all_cancelled_orders_service(mock_db, "buyer1")

    assert mock_db.execute_insert_update_delete.call_count == 6

    assert result["status"] == 200


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


def test_delete_order_input(mock_db):
    delete_order_input(mock_db, "order1")

    mock_db.execute_insert_update_delete.assert_called_once()

    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["order_id"] == "order1"