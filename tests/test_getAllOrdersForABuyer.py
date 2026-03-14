import pytest
from unittest.mock import MagicMock
from datetime import date
from app.services.orderdb import get_orders_for_buyer_db


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


def test_get_orders_for_buyer_not_found(mock_db):
    mock_db.execute_query.return_value = None

    result = get_orders_for_buyer_db(mock_db, "buyer1")

    assert result is None


def test_get_orders_for_buyer_no_orders(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        []
    ]

    result = get_orders_for_buyer_db(mock_db, "buyer1")

    assert result == []


def test_get_orders_for_buyer_single_order(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        [
            (
                "order1",
                "CREATED",
                date(2026, 3, 7),
                date(2026, 3, 10),
                "AUD",
                2,
                150.00
            )
        ]
    ]

    result = get_orders_for_buyer_db(mock_db, "buyer1")

    assert len(result) == 1
    assert result[0]["orderId"] == "order1"
    assert result[0]["status"] == "CREATED"
    assert result[0]["orderDate"] == "2026-03-07"
    assert result[0]["deliveryDate"] == "2026-03-10"
    assert result[0]["currencyCode"] == "AUD"
    assert result[0]["itemCount"] == 2
    assert result[0]["totalAmount"] == "150.0"


def test_get_orders_for_buyer_multiple_orders(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        [
            (
                "order1",
                "CREATED",
                date(2026, 3, 7),
                date(2026, 3, 10),
                "AUD",
                2,
                150.00
            ),
            (
                "order2",
                "CANCELED",
                date(2026, 3, 8),
                date(2026, 3, 11),
                "USD",
                1,
                75.00
            )
        ]
    ]

    result = get_orders_for_buyer_db(mock_db, "buyer1")

    assert len(result) == 2

    assert result[0]["orderId"] == "order1"
    assert result[0]["status"] == "CREATED"
    assert result[1]["orderId"] == "order2"
    assert result[1]["status"] == "CANCELED"


def test_get_orders_for_buyer_none_dates(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        [
            (
                "order1",
                "CREATED",
                None,
                None,
                "AUD",
                2,
                150.00
            )
        ]
    ]

    result = get_orders_for_buyer_db(mock_db, "buyer1")

    assert len(result) == 1
    assert result[0]["orderDate"] is None
    assert result[0]["deliveryDate"] is None


def test_get_orders_for_buyer_none_total_amount(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        [
            (
                "order1",
                "CREATED",
                date(2026, 3, 7),
                date(2026, 3, 10),
                "AUD",
                2,
                None
            )
        ]
    ]

    result = get_orders_for_buyer_db(mock_db, "buyer1")

    assert len(result) == 1
    assert result[0]["totalAmount"] == "0"


def test_get_orders_for_buyer_converts_order_id_and_total_amount_to_string(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        [
            (
                123,
                "CREATED",
                date(2026, 3, 7),
                date(2026, 3, 10),
                "AUD",
                2,
                150.75
            )
        ]
    ]

    result = get_orders_for_buyer_db(mock_db, "buyer1")

    assert result[0]["orderId"] == "123"
    assert result[0]["totalAmount"] == "150.75"


def test_get_orders_for_buyer_passes_status_filter(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        []
    ]

    get_orders_for_buyer_db(mock_db, "buyer1", status="CREATED")

    second_call_args = mock_db.execute_query.call_args_list[1][0]
    query = second_call_args[0]
    params = second_call_args[1]

    assert "UPPER(o.status) = UPPER(%(status)s)" in query
    assert params["status"] == "CREATED"


def test_get_orders_for_buyer_strips_status_filter(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        []
    ]

    get_orders_for_buyer_db(mock_db, "buyer1", status="  CREATED  ")

    second_call_args = mock_db.execute_query.call_args_list[1][0]
    params = second_call_args[1]

    assert params["status"] == "CREATED"


def test_get_orders_for_buyer_passes_from_date_filter(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        []
    ]

    get_orders_for_buyer_db(mock_db, "buyer1", from_date="2026-03-01")

    second_call_args = mock_db.execute_query.call_args_list[1][0]
    query = second_call_args[0]
    params = second_call_args[1]

    assert "o.order_date >= %(from_date)s::date" in query
    assert params["from_date"] == "2026-03-01"


def test_get_orders_for_buyer_passes_to_date_filter(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        []
    ]

    get_orders_for_buyer_db(mock_db, "buyer1", to_date="2026-03-31")

    second_call_args = mock_db.execute_query.call_args_list[1][0]
    query = second_call_args[0]
    params = second_call_args[1]

    assert "o.order_date <= %(to_date)s::date" in query
    assert params["to_date"] == "2026-03-31"


def test_get_orders_for_buyer_passes_limit_and_offset(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        []
    ]

    get_orders_for_buyer_db(mock_db, "buyer1", limit=5, offset=10)

    second_call_args = mock_db.execute_query.call_args_list[1][0]
    params = second_call_args[1]

    assert params["limit"] == 5
    assert params["offset"] == 10


def test_get_orders_for_buyer_calls_db_twice(mock_db):
    mock_db.execute_query.side_effect = [
        [(1,)],
        []
    ]

    get_orders_for_buyer_db(mock_db, "buyer1")

    assert mock_db.execute_query.call_count == 2