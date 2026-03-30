import pytest
from unittest.mock import MagicMock, patch
from app.services.order_service import (
    get_full_order_service,
    create_order_v2_service,
    _resolve_updated_address,
    _resolve_updated_product,
    update_order_service,
)

@pytest.fixture
def mock_db():
    return MagicMock()


def test_get_full_order_service_not_found(monkeypatch, mock_db):
    monkeypatch.setattr("app.services.order_service.get_full_order", lambda db, b, o: None)
    result = get_full_order_service(mock_db, "buyer-1", "order-1")
    assert result is None


def test_get_full_order_service_returns_mapped_dict(monkeypatch, mock_db):
    from datetime import date

    fake_row = [
        date(2026, 3, 7),
        date(2026, 3, 10),
        "AUD",
        "CREATED",
        "123 Main St", "Sydney", "NSW", "2000", "AU",
        [{"item_name": "Bolt", "quantity": 2}]
    ]
    monkeypatch.setattr("app.services.order_service.get_full_order", lambda db, b, o: fake_row)

    result = get_full_order_service(mock_db, "buyer-1", "order-1")

    assert result["order_date"] == "2026-03-07"
    assert result["delivery_date"] == "2026-03-10"
    assert result["currency_code"] == "AUD"
    assert result["status"] == "CREATED"
    assert result["address"]["street"] == "123 Main St"
    assert result["address"]["city"] == "Sydney"
    assert result["address"]["state"] == "NSW"
    assert result["address"]["postal_code"] == "2000"
    assert result["address"]["country_code"] == "AU"
    assert result["items"][0]["item_name"] == "Bolt"


def test_get_full_order_service_calls_get_full_order(monkeypatch, mock_db):
    calls = []
    monkeypatch.setattr(
        "app.services.order_service.get_full_order",
        lambda db, b, o: calls.append((b, o)) or None
    )
    get_full_order_service(mock_db, "buyer-1", "order-1")
    assert calls == [("buyer-1", "order-1")]


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
    assert "error" in result[0]


def test_create_order_v2_no_data_does_not_touch_db(mock_db):
    create_order_v2_service(mock_db, None, "buyer-001")
    mock_db.execute_query.assert_not_called()
    mock_db.execute_insert_update_delete.assert_not_called()


def test_create_order_v2_buyer_not_found_returns_404(monkeypatch, mock_db, valid_order_data):
    monkeypatch.setattr("app.services.order_service.get_buyer_by_id", lambda db, b: None)
    result = create_order_v2_service(mock_db, valid_order_data, "buyer-001")
    assert isinstance(result, tuple)
    assert result[1] == 404
    assert result[0]["error"] == "Buyer not found"


def test_create_order_v2_returns_order_id_and_buyer_data(monkeypatch, mock_db, valid_order_data):
    fake_buyer = {"buyer_id": "buyer-001", "party_name": "Test Corp",
                  "address": None, "contact": None, "tax_scheme": None,
                  "customer_assigned_account_id": "ACC01",
                  "supplier_assigned_account_id": None}
    monkeypatch.setattr("app.services.order_service.get_buyer_by_id", lambda db, b: fake_buyer)
    monkeypatch.setattr("app.services.order_service.insert_address", lambda db, a: [("addr-id",)])
    monkeypatch.setattr("app.services.order_service.insert_product", lambda db, i: {"Widget A": 101})
    monkeypatch.setattr("app.services.order_service.insert_order_v2", lambda db, d, b, a: [("order-999",)])
    monkeypatch.setattr("app.services.order_service.insert_order_item", lambda db, i, o, p: None)

    result = create_order_v2_service(mock_db, valid_order_data, "buyer-001")

    assert isinstance(result, dict)
    assert result["order_id"] == "order-999"
    assert result["buyer_data"] == fake_buyer


def test_create_order_v2_inserts_order_item(monkeypatch, mock_db, valid_order_data):
    item_calls = []
    fake_buyer = {"buyer_id": "b1", "party_name": "Corp", "address": None,
                  "contact": None, "tax_scheme": None,
                  "customer_assigned_account_id": None, "supplier_assigned_account_id": None}
    monkeypatch.setattr("app.services.order_service.get_buyer_by_id", lambda db, b: fake_buyer)
    monkeypatch.setattr("app.services.order_service.insert_address", lambda db, a: [("addr-id",)])
    monkeypatch.setattr("app.services.order_service.insert_product", lambda db, i: {"Widget A": 101})
    monkeypatch.setattr("app.services.order_service.insert_order_v2", lambda db, d, b, a: [("order-1",)])
    monkeypatch.setattr(
        "app.services.order_service.insert_order_item",
        lambda db, items, order_id, pmap: item_calls.append(order_id)
    )

    create_order_v2_service(mock_db, valid_order_data, "buyer-001")
    assert item_calls == ["order-1"]


def test_resolve_updated_address_uses_existing_address_when_found(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.order_service.get_existing_address_by_order",
        lambda db, o: ["10 Old St", "Melbourne", "VIC", "3000", "AU"]
    )
    monkeypatch.setattr(
        "app.services.order_service.find_address_by_fields",
        lambda db, merged: [("existing-addr-id",)]
    )

    result = _resolve_updated_address(mock_db, {"street": "10 Old St"}, "order-1")
    assert result == [("existing-addr-id",)]


def test_resolve_updated_address_creates_new_when_not_found(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.order_service.get_existing_address_by_order",
        lambda db, o: ["10 Old St", "Melbourne", "VIC", "3000", "AU"]
    )
    monkeypatch.setattr(
        "app.services.order_service.find_address_by_fields",
        lambda db, merged: None
    )
    monkeypatch.setattr(
        "app.services.order_service.upsert_address",
        lambda db, merged: [("new-addr-id",)]
    )

    result = _resolve_updated_address(mock_db, {"city": "Sydney"}, "order-1")
    assert result == [("new-addr-id",)]


def test_resolve_updated_address_merges_partial_update(monkeypatch, mock_db):
    captured = {}
    monkeypatch.setattr(
        "app.services.order_service.get_existing_address_by_order",
        lambda db, o: ["10 Old St", "Melbourne", "VIC", "3000", "AU"]
    )
    def fake_find(db, merged):
        captured.update(merged)
        return None
    monkeypatch.setattr("app.services.order_service.find_address_by_fields", fake_find)
    monkeypatch.setattr("app.services.order_service.upsert_address", lambda db, m: [("id",)])

    
    _resolve_updated_address(mock_db, {"city": "Sydney"}, "order-1")

    assert captured["street"] == "10 Old St"   
    assert captured["city"] == "Sydney"         
    assert captured["state"] == "VIC"           
    assert captured["postal_code"] == "3000"    
    assert captured["country_code"] == "AU"     


def test_resolve_updated_address_full_override(monkeypatch, mock_db):
    captured = {}
    monkeypatch.setattr(
        "app.services.order_service.get_existing_address_by_order",
        lambda db, o: ["10 Old St", "Melbourne", "VIC", "3000", "AU"]
    )
    def fake_find(db, merged):
        captured.update(merged)
        return None
    monkeypatch.setattr("app.services.order_service.find_address_by_fields", fake_find)
    monkeypatch.setattr("app.services.order_service.upsert_address", lambda db, m: [("id",)])

    new_address = {
        "street": "1 New Rd", "city": "Brisbane",
        "state": "QLD", "postal_code": "4000", "country_code": "AU"
    }
    _resolve_updated_address(mock_db, new_address, "order-1")

    assert captured["street"] == "1 New Rd"
    assert captured["city"] == "Brisbane"
    assert captured["state"] == "QLD"
    assert captured["postal_code"] == "4000"


def test_resolve_updated_product_returns_duplicate_if_found(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.order_service.find_duplicate_product",
        lambda db, item: [("existing-product-id",)]
    )
    result = _resolve_updated_product(mock_db, {"item_name": "Bolt", "unit_price": 1.5})
    assert result == [("existing-product-id",)]


def test_resolve_updated_product_creates_new_when_no_duplicate(monkeypatch, mock_db):
    monkeypatch.setattr("app.services.order_service.find_duplicate_product", lambda db, item: None)
    monkeypatch.setattr(
        "app.services.order_service.update_product",
        lambda db, item: [("new-product-id",)]
    )
    result = _resolve_updated_product(mock_db, {"item_name": "Bolt", "unit_price": 1.5, "product_id": "p1"})
    assert result == [("new-product-id",)]


def test_resolve_updated_product_raises_if_update_returns_none(monkeypatch, mock_db):
    monkeypatch.setattr("app.services.order_service.find_duplicate_product", lambda db, item: None)
    monkeypatch.setattr("app.services.order_service.update_product", lambda db, item: None)

    with pytest.raises(ValueError, match="invalid"):
        _resolve_updated_product(mock_db, {"item_name": "Ghost", "product_id": "bad-id"})


def test_resolve_updated_product_does_not_call_update_when_duplicate_found(monkeypatch, mock_db):
    update_calls = []
    monkeypatch.setattr(
        "app.services.order_service.find_duplicate_product",
        lambda db, item: [("dup-id",)]
    )
    monkeypatch.setattr(
        "app.services.order_service.update_product",
        lambda db, item: update_calls.append(item) or [("p",)]
    )
    _resolve_updated_product(mock_db, {"item_name": "Bolt"})
    assert update_calls == []


def test_update_order_service_missing_product_id_returns_400(monkeypatch, mock_db):
    result = update_order_service(
        mock_db,
        {"item": {"item_name": "Bolt", "quantity": 5}},  
        "buyer-1", "order-1"
    )
    assert isinstance(result, tuple)
    assert result[1] == 400
    assert result[0]["error"] == "please provide a valid product_id"


def test_update_order_service_invalid_product_uuid_returns_400(monkeypatch, mock_db):
    result = update_order_service(
        mock_db,
        {"item": {"item_name": "Bolt", "product_id": "not-a-uuid"}},
        "buyer-1", "order-1"
    )
    assert isinstance(result, tuple)
    assert result[1] == 400
    assert "uuid" in result[0]["error"].lower()


def test_update_order_service_address_resolved(monkeypatch, mock_db):
    captured = {}
    monkeypatch.setattr(
        "app.services.order_service._resolve_updated_address",
        lambda db, addr, order_id: captured.update({"called": True}) or [("addr-id",)]
    )
    monkeypatch.setattr("app.services.order_service.update_order", lambda db, d, b, o: d)

    result = update_order_service(
        mock_db,
        {"address": {"street": "1 New Rd", "city": "Sydney",
                     "state": "NSW", "postal_code": "2000", "country_code": "AU"}},
        "buyer-1", "order-1"
    )
    assert captured.get("called") is True


def test_update_order_service_invalid_product_raises_value_error(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.order_service._resolve_updated_product",
        lambda db, item: (_ for _ in ()).throw(ValueError("The product id provided is invalid"))
    )
    result = update_order_service(
        mock_db,
        {"item": {"product_id": "f5b163a5-b189-4666-8666-9527705b6ce9",
                  "item_name": "Bad", "quantity": 1}},
        "buyer-1", "order-1"
    )
    assert isinstance(result, tuple)
    assert result[1] == 400
    assert "invalid" in result[0]["error"].lower()


def test_update_order_service_item_update_fails_returns_400(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.order_service._resolve_updated_product",
        lambda db, item: [("prod-id",)]
    )
    monkeypatch.setattr(
        "app.services.order_service.update_order_items",
        lambda db, order_id, item, product_id: None  
    )

    result = update_order_service(
        mock_db,
        {"item": {"product_id": "f5b163a5-b189-4666-8666-9527705b6ce9",
                  "item_name": "Widget", "quantity": 5}},
        "buyer-1", "order-1"
    )
    assert isinstance(result, tuple)
    assert result[1] == 400
    assert "invalid product id" in result[0]["error"].lower()


def test_update_order_service_no_item_no_address_calls_update_order(monkeypatch, mock_db):
    update_calls = []
    monkeypatch.setattr(
        "app.services.order_service.update_order",
        lambda db, d, b, o: update_calls.append((b, o)) or {"order_id": o}
    )
    result = update_order_service(mock_db, {"order_date": "2026-01-01"}, "buyer-1", "order-1")
    assert update_calls == [("buyer-1", "order-1")]


def test_update_order_service_success_with_item(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.order_service._resolve_updated_product",
        lambda db, item: [("prod-id",)]
    )
    monkeypatch.setattr(
        "app.services.order_service.update_order_items",
        lambda db, order_id, item, product_id: {"updated": True}
    )
    monkeypatch.setattr(
        "app.services.order_service.update_order",
        lambda db, d, b, o: {"order_id": o}
    )

    result = update_order_service(
        mock_db,
        {"item": {"product_id": "f5b163a5-b189-4666-8666-9527705b6ce9",
                  "item_name": "Widget", "quantity": 5}},
        "buyer-1", "order-1"
    )
    assert result == {"order_id": "order-1"}


def test_update_order_service_success_with_address_and_item(monkeypatch, mock_db):
    monkeypatch.setattr(
        "app.services.order_service._resolve_updated_address",
        lambda db, addr, order_id: [("addr-id",)]
    )
    monkeypatch.setattr(
        "app.services.order_service._resolve_updated_product",
        lambda db, item: [("prod-id",)]
    )
    monkeypatch.setattr(
        "app.services.order_service.update_order_items",
        lambda db, order_id, item, product_id: {"updated": True}
    )
    monkeypatch.setattr(
        "app.services.order_service.update_order",
        lambda db, d, b, o: {"order_id": o}
    )

    result = update_order_service(
        mock_db,
        {
            "address": {"street": "1 New Rd", "city": "Sydney",
                        "state": "NSW", "postal_code": "2000", "country_code": "AU"},
            "item": {"product_id": "f5b163a5-b189-4666-8666-9527705b6ce9",
                     "item_name": "Widget", "quantity": 3}
        },
        "buyer-1", "order-1"
    )
    assert result == {"order_id": "order-1"}
    