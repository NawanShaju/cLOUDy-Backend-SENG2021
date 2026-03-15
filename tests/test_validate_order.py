import pytest
from app.services.validate_order import validate_order

@pytest.fixture
def valid_data():
    return {
        "order_date": "2024-01-15",
        "delivery_date": "2024-01-20",
        "currency_code": "USD",
        "address": {
            "street": "123 Main St",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000"
        },
        "items": [
            {
                "item_name": "Widget A",
                "unit_price": 10.00,
                "quantity": 2
            }
        ]
    }

def test_validate_order_no_buyer_id(valid_data):
    result = validate_order(valid_data, None)
    assert result is not None

def test_validate_order_valid_buyer_id(valid_data):
    result = validate_order(valid_data, "buyer-001")
    assert result is None

def test_validate_order_no_address(valid_data):
    valid_data.pop("address")
    result = validate_order(valid_data, "buyer-001")
    assert result is not None

def test_validate_order_missing_street(valid_data):
    valid_data["address"].pop("street")
    result = validate_order(valid_data, "buyer-001")
    assert "street" in result

def test_validate_order_missing_city(valid_data):
    valid_data["address"].pop("city")
    result = validate_order(valid_data, "buyer-001")
    assert "city" in result

def test_validate_order_missing_state(valid_data):
    valid_data["address"].pop("state")
    result = validate_order(valid_data, "buyer-001")
    assert "state" in result

def test_validate_order_missing_postal_code(valid_data):
    valid_data["address"].pop("postal_code")
    result = validate_order(valid_data, "buyer-001")
    assert "postal_code" in result

def test_validate_order_missing_order_date(valid_data):
    valid_data.pop("order_date")
    result = validate_order(valid_data, "buyer-001")
    assert "order_date" in result

def test_validate_order_missing_delivery_date(valid_data):
    valid_data.pop("delivery_date")
    result = validate_order(valid_data, "buyer-001")
    assert "delivery_date" in result

def test_validate_order_missing_currency_code(valid_data):
    valid_data.pop("currency_code")
    result = validate_order(valid_data, "buyer-001")
    assert "currency_code" in result

def test_validate_order_no_items(valid_data):
    valid_data.pop("items")
    result = validate_order(valid_data, "buyer-001")
    assert result is not None

def test_validate_order_single_item_as_dict(valid_data):
    valid_data["items"] = {"item_name": "Widget A", "unit_price": 10.00, "quantity": 2}
    result = validate_order(valid_data, "buyer-001")
    assert result is None

def test_validate_order_missing_item_name(valid_data):
    valid_data["items"][0].pop("item_name")
    result = validate_order(valid_data, "buyer-001")
    assert "item_name" in result

def test_validate_order_quantity_is_zero(valid_data):
    valid_data["items"][0]["quantity"] = 0
    result = validate_order(valid_data, "buyer-001")
    assert "quantity" in result

def test_validate_order_quantity_is_negative(valid_data):
    valid_data["items"][0]["quantity"] = -1
    result = validate_order(valid_data, "buyer-001")
    assert "quantity" in result

def test_validate_order_quantity_is_not_integer(valid_data):
    valid_data["items"][0]["quantity"] = "two"
    result = validate_order(valid_data, "buyer-001")
    assert "quantity" in result

def test_validate_order_unit_price_is_negative(valid_data):
    valid_data["items"][0]["unit_price"] = -1
    result = validate_order(valid_data, "buyer-001")
    assert "unit_price" in result

def test_validate_order_unit_price_is_zero(valid_data):
    valid_data["items"][0]["unit_price"] = 0
    result = validate_order(valid_data, "buyer-001")
    assert result is None

def test_validate_order_unit_price_is_not_a_number(valid_data):
    valid_data["items"][0]["unit_price"] = "ten"
    result = validate_order(valid_data, "buyer-001")
    assert "unit_price" in result
    