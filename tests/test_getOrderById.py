import pytest
from unittest.mock import MagicMock
from app.services.orderdb import get_order_details


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


def test_get_order_details_not_found(mock_db):
    mock_db.execute_query.return_value = []

    result = get_order_details(mock_db, "buyer1", "order1")

    assert result is None


def test_get_order_details_no_xml(mock_db):
    order_rows = [
        ("order1", "CREATED", "prod1", "Bolt", "desc", 1.5, 10, 15)
    ]

    mock_db.execute_query.side_effect = [
        order_rows,
        None
    ]

    result = get_order_details(mock_db, "buyer1", "order1")

    assert result is None


def test_get_order_details_single_item(mock_db):
    order_rows = [
        ("order1", "CREATED", "prod1", "Bolt", "desc", 1.5, 10, 15)
    ]
    xml = "<Order></Order>"

    mock_db.execute_query.side_effect = [
        order_rows,
        [xml]
    ]

    result = get_order_details(mock_db, "buyer1", "order1")

    assert result["orderId"] == "order1"
    assert result["status"] == "CREATED"
    assert result["xml"] == xml
    assert len(result["items"]) == 1

    item = result["items"][0]
    assert item["productId"] == "prod1"
    assert item["productName"] == "Bolt"
    assert item["productDescription"] == "desc"
    assert item["unitPrice"] == "1.5"
    assert item["quantity"] == 10
    assert item["totalPrice"] == "15"


def test_get_order_details_multiple_items(mock_db):
    order_rows = [
        ("order1", "CANCELED", "prod1", "Bolt", "desc", 1.5, 10, 15),
        ("order1", "CANCELED", "prod2", "Nut", "desc2", 2.0, 5, 10)
    ]
    xml = "<Order></Order>"

    mock_db.execute_query.side_effect = [
        order_rows,
        [xml]
    ]

    result = get_order_details(mock_db, "buyer1", "order1")

    assert result["orderId"] == "order1"
    assert result["status"] == "CANCELED"
    assert result["xml"] == xml
    assert len(result["items"]) == 2

    assert result["items"][0]["productId"] == "prod1"
    assert result["items"][1]["productId"] == "prod2"


def test_get_order_details_none_values(mock_db):
    order_rows = [
        ("order1", "CREATED", None, "Bolt", None, None, 10, None)
    ]
    xml = "<Order></Order>"

    mock_db.execute_query.side_effect = [
        order_rows,
        [xml]
    ]

    result = get_order_details(mock_db, "buyer1", "order1")

    item = result["items"][0]

    assert result["orderId"] == "order1"
    assert result["status"] == "CREATED"
    assert item["productId"] is None
    assert item["productName"] == "Bolt"
    assert item["productDescription"] is None
    assert item["unitPrice"] is None
    assert item["quantity"] == 10
    assert item["totalPrice"] is None


def test_get_order_details_converts(mock_db):
    order_rows = [
        (123, "CREATED", 456, "Bolt", "desc", 1.5, 10, 15.75)
    ]
    xml = "<Order></Order>"

    mock_db.execute_query.side_effect = [
        order_rows,
        [xml]
    ]

    result = get_order_details(mock_db, "buyer1", "order1")

    item = result["items"][0]

    assert result["orderId"] == "123"
    assert item["productId"] == "456"
    assert item["unitPrice"] == "1.5"
    assert item["totalPrice"] == "15.75"


def test_get_order_details_calls_db_twice(mock_db):
    order_rows = [
        ("order1", "CREATED", "prod1", "Bolt", "desc", 1.5, 10, 15)
    ]
    xml = "<Order></Order>"

    mock_db.execute_query.side_effect = [
        order_rows,
        [xml]
    ]

    get_order_details(mock_db, "buyer1", "order1")

    assert mock_db.execute_query.call_count == 2