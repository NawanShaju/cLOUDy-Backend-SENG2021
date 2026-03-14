import pytest
from flask import Flask
from app.routes import api
from lxml import etree

API_HEADERS = {"api-key": "dummy-key"}

NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"


def cbc(tag):
    return f"{{{NS_CBC}}}{tag}"


def cac(tag):
    return f"{{{NS_CAC}}}{tag}"


class DummyDB:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute_query(self, query, params):
        return None

    def execute_insert_update_delete(self, query, params):
        return [("f5b163a5-b189-4666-8666-9527705b6ce9",)]


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

    monkeypatch.setattr("app.services.apiKey.PostgresDB", lambda: FakeAuthDB())


@pytest.fixture
def valid_order():
    return {
        "order_date": "2024-01-15",
        "delivery_date": "2024-01-20",
        "currency_code": "USD",
        "address": {
            "street": "123 Main St",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000",
            "country_code": "AU"
        },
        "items": [
            {
                "item_name": "Widget A",
                "item_description": "A great widget",
                "unit_price": 10.00,
                "quantity": 2
            }
        ]
    }


# ––––––––––––––––––––––––––––––––––––––––––––––– invalid requests ─────────────────────────────────────────────────────

def test_create_order_invalid_buyer_id(client, valid_order):
    response = client.post(
        "/v1/buyer/not-a-uuid/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 400
    assert "buyerId" in response.get_json()["error"]


def test_create_order_missing_json(client):
    response = client.post(
        "/v1/buyer/f5b163a5-b189-4666-8666-9527705b6ce9/order",
        json={},
        headers=API_HEADERS
    )
    assert response.status_code == 400


def test_create_order_missing_address(client, valid_order):
    valid_order.pop("address")
    response = client.post(
        "/v1/buyer/f5b163a5-b189-4666-8666-9527705b6ce9/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 400


def test_create_order_missing_items(client, valid_order):
    valid_order.pop("items")
    response = client.post(
        "/v1/buyer/f5b163a5-b189-4666-8666-9527705b6ce9/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 400


# –––––––––––––––––––––––––––––––––––––––––––––––– success ─────────────────────────────────────────────────────────────

def test_create_order_success_status_code(monkeypatch, client, valid_order):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    response = client.post(
        "/v1/buyer/f5b163a5-b189-4666-8666-9527705b6ce9/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 200


def test_create_order_success_returns_xml(monkeypatch, client, valid_order):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    response = client.post(
        "/v1/buyer/f5b163a5-b189-4666-8666-9527705b6ce9/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.content_type == "application/xml; charset=utf-8"


def test_create_order_success_xml_contains_order_id(monkeypatch, client, valid_order):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    response = client.post(
        "/v1/buyer/f5b163a5-b189-4666-8666-9527705b6ce9/order",
        json=valid_order,
        headers=API_HEADERS
    )
    root = etree.fromstring(response.data)
    assert root.findtext(cbc("ID")) is not None


def test_create_order_success_xml_contains_buyer_id(monkeypatch, client, valid_order):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    response = client.post(
        "/v1/buyer/f5b163a5-b189-4666-8666-9527705b6ce9/order",
        json=valid_order,
        headers=API_HEADERS
    )
    root = etree.fromstring(response.data)
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PartyIdentification')}/{cbc('ID')}"
    assert root.findtext(path) == "f5b163a5-b189-4666-8666-9527705b6ce9"