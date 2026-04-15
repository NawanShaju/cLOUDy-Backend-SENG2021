import pytest
from unittest.mock import MagicMock
from flask import Flask
from app.services.order_service import create_order_service
from app.services.order_service import create_order_v2_service
from app.services.db_services.order_db import (
    insert_address,
    insert_product,
    insert_order,
    insert_order_item
)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def mock_db():
    return MagicMock()


# ––––––––––––––––––––––––––––––––––––––––––––––– create_order_service ──────────────────────────────────────────────────────

def test_create_order_no_data_returns_400(app, mock_db):
    with app.app_context():
        response, status_code = create_order_service(mock_db, None, "buyer-001", "test-api-key")
        assert status_code == 400


def test_create_order_no_data_returns_error_message(app, mock_db):
    with app.app_context():
        response, _ = create_order_service(mock_db, None, "buyer-001", "test-api-key")
        assert "error" in response.get_json()


def test_create_order_no_data_does_not_touch_db(app, mock_db):
    with app.app_context():
        create_order_service(mock_db, None, "buyer-001", "test-api-key")
        mock_db.execute_insert_update_delete.assert_not_called()


def test_create_order_returns_order_id(monkeypatch, mock_db):
    monkeypatch.setattr("app.services.order_service.insert_auth", lambda db, k, b: None)
    mock_db.execute_insert_update_delete.side_effect = [
        [(1,)],
        [(101,)],
        [(999,)],
        None,
    ]
    data = {
        "order_date": "2024-01-15",
        "delivery_date": "2024-01-20",
        "currency_code": "USD",
        "address": {"street": "123 Main St", "city": "Sydney", "state": "NSW", "postal_code": "2000", "country_code": "AU"},
        "items": [{"item_name": "Widget A", "item_description": "A widget", "unit_price": 10.00, "quantity": 2}]
    }
    result = create_order_service(mock_db, data, "buyer-001", "test-api-key")
    assert result == [(999,)]


# ––––––––––––––––––––––––––––––––––––––––––––––– insert_address ───────────────────────────────────────────────────────

def test_insert_address_calls_db(mock_db):
    mock_db.execute_insert_update_delete.return_value = [(1,)]
    address = {"street": "123 Main St", "city": "Sydney", "state": "NSW", "postal_code": "2000", "country_code": "AU"}
    result = insert_address(mock_db, address)
    mock_db.execute_insert_update_delete.assert_called_once()
    assert result == [(1,)]


def test_insert_address_returns_address_id(mock_db):
    mock_db.execute_insert_update_delete.return_value = [("uuid-address-id",)]
    address = {"street": "123 Main St", "city": "Sydney", "state": "NSW", "postal_code": "2000", "country_code": "AU"}
    result = insert_address(mock_db, address)
    assert result[0][0] == "uuid-address-id"


# –––––––––––––––––––––––––––––––––––––––––––––– insert_product ────────────────────────────────────────────────────────

def test_insert_product_returns_product_map(mock_db):
    mock_db.execute_insert_update_delete.return_value = [(101,)]
    items = [{"item_name": "Widget A", "item_description": "A widget", "unit_price": 10.00}]
    seller_id = "e8b12a38-feba-40e3-9245-1496f7f0794d"
    result = insert_product(mock_db, items, seller_id)
    assert result == {"Widget A": (101, )}


def test_insert_product_calls_db_once_per_item(mock_db):
    mock_db.execute_insert_update_delete.side_effect = [[(101,)], [(102,)]]
    items = [
        {"item_name": "Widget A", "item_description": "A widget", "unit_price": 10.00},
        {"item_name": "Widget B", "item_description": "B widget", "unit_price": 5.00}
    ]
    seller_id = "e8b12a38-feba-40e3-9245-1496f7f0794d"
    insert_product(mock_db, items, seller_id)
    assert mock_db.execute_insert_update_delete.call_count == 2


# ––––––––––––––––––––––––––––––––––––––––––––––– insert_order ─────────────────────────────────────────────────────────

def test_insert_order_calls_db(mock_db):
    mock_db.execute_insert_update_delete.return_value = [(999,)]
    data = {"order_date": "2024-01-15", "delivery_date": "2024-01-20", "currency_code": "USD"}
    result = insert_order(mock_db, data, "buyer-001", 1)
    mock_db.execute_insert_update_delete.assert_called_once()
    assert result == [(999,)]


def test_insert_order_status_is_created(mock_db):
    mock_db.execute_insert_update_delete.return_value = [(999,)]
    data = {"order_date": "2024-01-15", "delivery_date": "2024-01-20", "currency_code": "USD"}
    insert_order(mock_db, data, "buyer-001", 1)
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["status"] == "CREATED"


def test_insert_order_passes_correct_buyer_id(mock_db):
    mock_db.execute_insert_update_delete.return_value = [(999,)]
    data = {"order_date": "2024-01-15", "delivery_date": "2024-01-20", "currency_code": "USD"}
    insert_order(mock_db, data, "buyer-001", 1)
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["buyerId"] == "buyer-001"


# ––––––––––––––––––––––––––––––––––––––––––––––– insert_order_item ────────────────────────────────────────────────────

def test_insert_order_item_calls_db_once_per_item(mock_db):
    items = [
        {"item_name": "Widget A", "unit_price": 10.00, "quantity": 2},
        {"item_name": "Widget B", "unit_price": 5.00,  "quantity": 3}
    ]
    product_map = {"Widget A": 101, "Widget B": 102}
    insert_order_item(mock_db, items, 999, product_map)
    assert mock_db.execute_insert_update_delete.call_count == 2


def test_insert_order_item_calculates_total_price(mock_db):
    items = [{"item_name": "Widget A", "unit_price": 10.00, "quantity": 3}]
    product_map = {"Widget A": 101}
    insert_order_item(mock_db, items, 999, product_map)
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["total_price"] == 30.00


def test_insert_order_item_passes_correct_product_id(mock_db):
    items = [{"item_name": "Widget A", "unit_price": 10.00, "quantity": 2}]
    product_map = {"Widget A": 101}
    insert_order_item(mock_db, items, 999, product_map)
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["product_id"] == 101
    
# ––––––––––––––––––––––––––––––––––––––––––––––– create_order_v2_service ────────────────────────────────────────────────────    
    
@pytest.fixture
def valid_order_data():
    return {
        "order_date": "2024-01-15",
        "delivery_date": "2024-01-20",
        "currency_code": "AUD",
        "address": {
            "street": "123 Main St", "city": "Sydney",
            "state": "NSW", "postal_code": "2000", "country_code": "AU"
        },
        "items": [
            {"item_name": "Widget A", "item_description": "A widget",
             "unit_price": 10.00, "quantity": 2}
        ]
    }
 
 
def test_create_order_v2_no_data_returns_400(mock_db):
    result = create_order_v2_service(mock_db, None, "buyer-001")
    assert isinstance(result, tuple)
    assert result[1] == 400
 
 
def test_create_order_v2_no_data_returns_error(mock_db):
    result = create_order_v2_service(mock_db, None, "buyer-001")
    assert "error" in result[0]
 
 
def test_create_order_v2_buyer_not_found_returns_404(monkeypatch, mock_db, valid_order_data):
    monkeypatch.setattr(
        "app.services.order_service.get_buyer_by_id",
        lambda db, buyer_id: None
    )
    result = create_order_v2_service(mock_db, valid_order_data, "buyer-001")
    assert isinstance(result, tuple)
    assert result[1] == 404
    assert result[0]["error"] == "Buyer not found"
 
 
def test_create_order_v2_returns_order_id_and_buyer_data(monkeypatch, mock_db, valid_order_data):
    fake_buyer = {
        "buyer_id": "buyer-001",
        "party_name": "Test Corp",
        "address": None,
        "contact": None,
        "tax_scheme": None,
        "customer_assigned_account_id": "ACC01",
        "supplier_assigned_account_id": None,
    }
    monkeypatch.setattr("app.services.order_service.get_buyer_by_id", lambda db, b: fake_buyer)
    monkeypatch.setattr("app.services.order_service.insert_address", lambda db, a: [("addr-id",)])
    monkeypatch.setattr("app.services.order_service.insert_product", lambda db, i, seller_id: {"Widget A": 101})
    monkeypatch.setattr("app.services.order_service.insert_order_v2", lambda db, d, b, a: [("order-999",)])
    monkeypatch.setattr("app.services.order_service.insert_order_item", lambda db, i, o, p: None)
 
    result = create_order_v2_service(mock_db, valid_order_data, "buyer-001")
    assert isinstance(result, dict)
    assert result["order_id"] == "order-999"
    assert result["buyer_data"] == fake_buyer
 
 
def test_create_order_v2_does_not_touch_db_when_no_data(mock_db):
    create_order_v2_service(mock_db, None, "buyer-001")
    mock_db.execute_insert_update_delete.assert_not_called()
    mock_db.execute_query.assert_not_called()