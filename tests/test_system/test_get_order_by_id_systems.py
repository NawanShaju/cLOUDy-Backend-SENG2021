import pytest
from flask import Flask
from app.routes import api

API_HEADERS = {"api-key": "dummy-key"}

BUYER_ID = "70f4810c-5904-454c-8b35-2876e01d9b08"
ORDER_ID = "f5b163a5-b189-4666-8666-9527705b6ce9"
PRODUCT_ID_1 = "eacb6df6-8ab2-4899-80eb-4d790796c15b"
PRODUCT_ID_2 = "adcda6cf-36b0-40d5-b4c2-ed639dacfee4"


class SuccessDB:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute_query(self, query, params, fetch_all=False):
        if "FROM orders o" in query:
            return [
                (
                    ORDER_ID,
                    "CREATED",
                    PRODUCT_ID_1,
                    "Steel Bolt",
                    "High-strength bolt",
                    1.50,
                    10,
                    15.00
                ),
                (
                    ORDER_ID,
                    "CREATED",
                    PRODUCT_ID_2,
                    "Steel Nut",
                    "High-strength nut",
                    2.00,
                    5,
                    10.00
                )
            ]

        if "FROM order_documents" in query:
            return ["<Order>test xml</Order>"]

        return None


class NotFoundDB:
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

def test_get_order_by_id_invalid_order_id(client):
    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/not-a-uuid",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "orderId must be a valid UUID"


def test_get_order_by_id_not_found(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: NotFoundDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/{ORDER_ID}",
        headers=API_HEADERS
    )

    assert response.status_code == 404
    body = response.get_json()

    assert body["status"] == 404
    assert body["error"] == "Order couldnt be found"


def test_get_order_by_id_success_status_code(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/{ORDER_ID}",
        headers=API_HEADERS
    )

    assert response.status_code == 200


def test_get_order_by_id_success_returns_json(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/{ORDER_ID}",
        headers=API_HEADERS
    )

    assert response.is_json


def test_get_order_by_id_success_contains_order_id(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/{ORDER_ID}",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert body["orderId"] == ORDER_ID


def test_get_order_by_id_success_contains_status(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/{ORDER_ID}",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert body["status"] == "CREATED"


def test_get_order_by_id_success_contains_items(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/{ORDER_ID}",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert len(body["items"]) == 2
    assert body["items"][0]["productId"] == PRODUCT_ID_1
    assert body["items"][1]["productId"] == PRODUCT_ID_2


def test_get_order_by_id_success_contains_product_names(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/{ORDER_ID}",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert body["items"][0]["productName"] == "Steel Bolt"
    assert body["items"][1]["productName"] == "Steel Nut"


def test_get_order_by_id_success_contains_xml(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: SuccessDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/{ORDER_ID}",
        headers=API_HEADERS
    )

    body = response.get_json()

    assert body["xml"] == "<Order>test xml</Order>"


def test_get_order_by_id_internal_server_error(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: ErrorDB())

    response = client.get(
        f"/v1/buyer/{BUYER_ID}/order/{ORDER_ID}",
        headers=API_HEADERS
    )

    assert response.status_code == 500
    body = response.get_json()

    assert body["status"] == 500
    assert body["error"] == "Database crashed"