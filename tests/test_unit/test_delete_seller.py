import pytest
from unittest.mock import MagicMock
from app.services.seller_service import delete_seller_service
from app.services.db_services.seller_db import seller_has_existing_orders, delete_seller


@pytest.fixture
def mock_db():
    return MagicMock()


def test_delete_seller_not_found_returns_404(monkeypatch, mock_db):
    monkeypatch.setattr("app.services.seller_service.get_seller_by_id", lambda db, seller_id: None)

    result = delete_seller_service(mock_db, "missing-id")

    assert isinstance(result, tuple)
    assert result[1] == 404
    assert result[0]["error"] == "Seller not found"


def test_delete_seller_with_existing_orders_returns_409(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.seller_service.get_seller_by_id",
        lambda db, seller_id: {"seller_id": seller_id}
    )
    monkeypatch.setattr(
        "app.services.seller_service.seller_has_existing_orders",
        lambda db, seller_id: True
    )

    result = delete_seller_service(mock_db, "seller-uuid-1234")

    assert isinstance(result, tuple)
    assert result[1] == 409
    assert "hard deleted first" in result[0]["error"]


def test_delete_seller_success_returns_dict(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.seller_service.get_seller_by_id",
        lambda db, seller_id: {"seller_id": seller_id}
    )
    monkeypatch.setattr(
        "app.services.seller_service.seller_has_existing_orders",
        lambda db, seller_id: False
    )
    monkeypatch.setattr(
        "app.services.seller_service.delete_seller",
        lambda db, seller_id: [("seller-uuid-1234",)]
    )

    result = delete_seller_service(mock_db, "seller-uuid-1234")

    assert isinstance(result, dict)
    assert result["seller_id"] == "seller-uuid-1234"
    assert result["message"] == "Seller deleted successfully"


def test_delete_seller_db_failure_returns_500(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.seller_service.get_seller_by_id",
        lambda db, seller_id: {"seller_id": seller_id}
    )
    monkeypatch.setattr(
        "app.services.seller_service.seller_has_existing_orders",
        lambda db, seller_id: False
    )
    monkeypatch.setattr(
        "app.services.seller_service.delete_seller",
        lambda db, seller_id: None
    )

    result = delete_seller_service(mock_db, "seller-uuid-1234")

    assert isinstance(result, tuple)
    assert result[1] == 500
    assert result[0]["error"] == "Failed to delete seller"


def test_seller_has_existing_orders_calls_db(mock_db):
    mock_db.execute_query.return_value = [("1",)]

    result = seller_has_existing_orders(mock_db, "seller-uuid-1234")

    mock_db.execute_query.assert_called_once()
    assert result is True


def test_seller_has_existing_orders_returns_false_when_none(mock_db):
    mock_db.execute_query.return_value = None

    result = seller_has_existing_orders(mock_db, "seller-uuid-1234")

    assert result is False


def test_delete_seller_calls_db(mock_db):
    mock_db.execute_insert_update_delete.return_value = [("seller-uuid-1234",)]

    result = delete_seller(mock_db, "seller-uuid-1234")

    mock_db.execute_insert_update_delete.assert_called_once()
    assert result == [("seller-uuid-1234",)]