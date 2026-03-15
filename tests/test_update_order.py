import pytest
from unittest.mock import MagicMock
from app.services.order_db import (
    update_address,
    update_order_input,
    update_order_product,
    update_order_items,
    get_full_order_db
)

@pytest.fixture
def mock_db():
    db = MagicMock()
    return db

def test_update_address_only_state(mock_db):
    mock_db.execute_query.side_effect = [
        ['123 Main St', 'Sydney', 'NSW', '2000', 'AU'],
        [] 
    ]
    mock_db.execute_insert_update_delete.return_value = [('uuid-address-id',)]

    address_update = {"state": "VIC"}

    result = update_address(mock_db, address_update, 'f5b163a5-b189-4666-8666-9527705b6ce9')
    
    assert mock_db.execute_query.call_count == 2
    mock_db.execute_insert_update_delete.assert_called_once()
    assert result[0][0] == 'uuid-address-id'


def test_update_input_order(mock_db):
    mock_db.execute_insert_update_delete.return_value = [{'order_id': 'f5b163a5-b189-4666-8666-9527705b6ce9'}]

    data = {
        "order_date": "2026-03-07",
        "delivery_date": "2026-03-10"
    }

    result = update_order_input(
        mock_db, 
        data, 
        '70f4810c-5904-454c-8b35-2876e01d9b08', 
        'f5b163a5-b189-4666-8666-9527705b6ce9'
    )

    mock_db.execute_insert_update_delete.assert_called_once()
    assert result == [{'order_id': 'f5b163a5-b189-4666-8666-9527705b6ce9'}]


def test_update_order_products(mock_db):
    mock_db.execute_query.return_value = None
    mock_db.execute_insert_update_delete.return_value = [('p1',)]

    items = {
        "item_name": "Steel Bolt",
        "item_description": "desc",
        "unit_price": 10,
        "product_id": 1 
    }

    result = update_order_product(mock_db, items)

    mock_db.execute_insert_update_delete.assert_called_once()
    assert result[0][0] == 'p1'


def test_update_order_items(mock_db):
    items = {
        "item_name": "Steel Bolt",
        "quantity": 5,
        "unit_price": 10
    }
    product_id = 1  

    update_order_items(
        mock_db, 
        'f5b163a5-b189-4666-8666-9527705b6ce9', 
        items, 
        product_id
    )

    mock_db.execute_insert_update_delete.assert_called_once()
    params = mock_db.execute_insert_update_delete.call_args[0][1]
    assert params["total_price"] == 50
    assert params["quantity"] == 5
    assert params["product_id"] == 1


def test_update_order_get_full_order(mock_db):
    from datetime import datetime
    order_date = datetime(2026, 3, 7)
    delivery_date = datetime(2026, 3, 10)

    row = [order_date, delivery_date, 'AUD', 'CREATED', '123 St', 'Sydney', 'NSW', '2000', 'AU', [{"item_name": "Bolt", "quantity": 2}]]
    mock_db.execute_query.return_value = row

    result = get_full_order_db(mock_db, '70f4810c-5904-454c-8b35-2876e01d9b08', 'f5b163a5-b189-4666-8666-9527705b6ce9')

    assert result["order_date"] == order_date.isoformat()
    assert result["delivery_date"] == delivery_date.isoformat()
    assert result["currency_code"] == 'AUD'
    assert result["status"] == 'CREATED'
    assert result["address"]["city"] == 'Sydney'
    assert result["items"][0]["item_name"] == "Bolt"


def test_update_order_none(mock_db):
    mock_db.execute_query.return_value = None
    result = get_full_order_db(mock_db, '70f4810c-5904-454c-8b35-2876e01d9b08', 'f5b163a5-b189-4666-8666-9527705b6ce9')
    assert result is None