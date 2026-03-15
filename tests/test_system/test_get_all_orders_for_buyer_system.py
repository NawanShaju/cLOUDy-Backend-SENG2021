import pytest
from flask import Flask
from app.routes import api

API_HEADERS = {"api-key": "dummy-key"}

BUYER_ID = "70f4810c-5904-454c-8b35-2876e01d9b08"
ORDER_ID_1 = "ca21f797-379a-4e27-a703-4992c5ea46fa"
ORDER_ID_2 = "f5b163a5-b189-4666-8666-9527705b6ce9"


class SuccessDB:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute_query(self, query, params, fetch_all=False):
        if "SELECT 1" in query:
            return [(1,)]

        if "FROM orders o" in query:
            return [
                (
                    ORDER_ID_1,
                    "CREATED",
                    FakeDate("2026-03-07"),
                    FakeDate("2026-03-10"),
                    "AUD",
                    2,
                    150.00
                ),
                (
                    ORDER_ID_2,
                    "CREATED",
                    FakeDate("2026-03-07"),
                    FakeDate("2026-03-10"),
                    "USD",
                    2,
                    150.00
                )
            ]

        return []


class EmptyOrdersDB:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute_query(self, query, params, fetch_all=False):
        if "SELECT 1" in query:
            return [(1,)]

        if "FROM orders o" in query:
            return []

        return []


class BuyerNotFoundDB:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute_query(self, query, params, fetch_all=False):
        return []


class ErrorDB:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute_query(self, query, params, fetch_all=False):
        raise Exception("Database crashed")


class FakeDate:
    def __init__(self, value):
        self.value = value

    def isoformat(self):
        return self.value


@pytest.fixture
def app():
    test_app = Flask(__name__)
    test_app.register_blueprint(api)
    return test_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def mock_auth_db(monkeypatch):
    class FakeAuthDB:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute_query(self, query, params):
            return [("dummy-key",)]

    monkeypatch.setattr("app.services.api_key.PostgresDB", lambda: FakeAuthDB())


def test_get_orders_for_buyer_invalid_buyer_id(client):
    response = client.get(
        "/v1/buyer/not-a-uuid/order",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "buyerId must be a valid UUID"


def test_get_orders_for_buyer_invalid_limit_type(client):
    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order?limit=abc",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    body = response.get_json()

    assert body["status"] == 400
    assert body["error"] == "limit and offset must be integers"


def test_get_orders_for_buyer_invalid_offset_type(client):
    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order?offset=abc",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    body = response.get_json()

    assert body["status"] == 400
    assert body["error"] == "limit and offset must be integers"


def test_get_orders_for_buyer_invalid_limit_value(client):
    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order?limit=0",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    body = response.get_json()

    assert body["status"] == 400
    assert body["error"] == "limit must be greater than 0 and offset must be 0 or more"


def test_get_orders_for_buyer_invalid_offset_value(client):
    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order?offset=-1",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    body = response.get_json()

    assert body["status"] == 400
    assert body["error"] == "limit must be greater than 0 and offset must be 0 or more"


def test_get_orders_for_buyer_invalid_from_date(client):
    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order?fromDate=not-a-date",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    body = response.get_json()

    assert body["status"] == 400
    assert "date" in body["error"].lower()


def test_get_orders_for_buyer_invalid_to_date(client):
    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order?toDate=not-a-date",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    body = response.get_json()

    assert body["status"] == 400
    assert "date" in body["error"].lower()


def test_get_orders_for_buyer_not_found(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: BuyerNotFoundDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order",
        headers=API_HEADERS
    )

    assert response.status_code == 404
    body = response.get_json()

    assert body["status"] == 404
    assert body["error"] == "Buyer not found"


def test_get_orders_for_buyer_success_status_code(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order",
        headers=API_HEADERS
    )

    assert response.status_code == 200


def test_get_orders_for_buyer_success_returns_json(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order",
        headers=API_HEADERS
    )

    assert response.is_json


def test_get_orders_for_buyer_success_contains_buyer_id(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert body["buyerId"] == BUYER_ID


def test_get_orders_for_buyer_success_contains_message(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert body["message"] == "All orders for a buyer"


def test_get_orders_for_buyer_success_contains_count(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert body["count"] == 2


def test_get_orders_for_buyer_success_contains_limit_and_offset(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order?limit=5&offset=2",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert body["limit"] == 5
    assert body["offset"] == 2


def test_get_orders_for_buyer_success_contains_orders(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert len(body["orders"]) == 2
    assert body["orders"][0]["orderId"] == ORDER_ID_1
    assert body["orders"][1]["orderId"] == ORDER_ID_2


def test_get_orders_for_buyer_success_contains_status_filter(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order?status=CREATED",
        headers=API_HEADERS
    )

    assert response.status_code == 200
    body = response.get_json()

    assert body["count"] == 2
    assert body["orders"][0]["status"] == "CREATED"
    assert body["orders"][1]["status"] == "CREATED"


def test_get_orders_for_buyer_success_empty_orders(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: EmptyOrdersDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order",
        headers=API_HEADERS
    )

    assert response.status_code == 200
    body = response.get_json()

    assert body["status"] == 200
    assert body["count"] == 0
    assert body["orders"] == []


def test_get_orders_for_buyer_internal_server_error(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: ErrorDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order",
        headers=API_HEADERS
    )

    assert response.status_code == 500
    body = response.get_json()

    assert body["status"] == 500
    assert body["error"] == "Database crashed"