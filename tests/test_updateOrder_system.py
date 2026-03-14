import pytest
from flask import Flask, jsonify, Response
from app.routes import api
import uuid 

API_HEADERS = {"api-key": "dummy-key"}

class DummyDB:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def execute_query(self, query, params):
        if "addresses a" in query:
            return [("123 Main St", "City", "State", "12345", "AU")]
        elif "products" in query:
            return [[1]] 
        elif "orders o" in query:
            return [(
                "2026-03-07", 
                "2026-03-10",
                "AUD",  
                "UPDATED",
                "123 Main St", "City", "State", "2000", "AU",
                [{"item_name": "Steel Bolt", "item_description": "desc", "unit_price": 10, "quantity": 5}]
            )]
        return None

    def execute_insert_update_delete(self, query, params):
        return [[1]] 


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


def valid_uuid():
    return str(uuid.uuid4())


def test_update_order(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr("app.routes.update_order_db", lambda db, data, b, o: True)
    monkeypatch.setattr("app.routes.get_full_order_db", lambda db, b, o: {
        "order_date": "2026-03-07",
        "delivery_date": "2026-03-10",
        "currency_code": "AUD",
        "status": "UPDATED",
        "address": {
            "street": "123 Main St",
            "city": "City",
            "state": "State",
            "postal_code": "12345",
            "country_code": "AU"
        },
        "items": [{"item_name": "Steel Bolt", "item_description": "desc", "unit_price": 10, "quantity": 5}]
    })
    monkeypatch.setattr("app.routes.generate_xml", lambda full_order, orderId, buyerId: "<Order>ok</Order>")
    monkeypatch.setattr("app.routes.xml_to_db_update_cancel", lambda db, xml_string, orderId: True)

    buyer_id = valid_uuid()
    order_id = valid_uuid()
    payload = {
        "address": {"street": "436 George St", "city": "Sydney", "state": "NSW", "postalCode": "2000", "countryCode": "AU"},
        "Quantity": 15
    }

    response = client.put(
        f"/v1/buyer/{buyer_id}/order/{order_id}",
        json=payload,
        headers=API_HEADERS
    )

    assert response.status_code == 200
    data = response.data.decode()
    assert "<Order>" in data


def test_update_order_invalid_json(client):
    buyer_id = valid_uuid()
    order_id = valid_uuid()
    
    response = client.put(
        f"/v1/buyer/{buyer_id}/order/{order_id}",
        json={},
        headers=API_HEADERS
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Invalid Json Provided"


def test_update_order_invalid_buyer_or_order_id(client):
    payload = {"Quantity": 10}
    
    response = client.put(
        "/v1/buyer/invalid-uuid/order/invalid-uuid",
        json=payload,
        headers=API_HEADERS
    )

    data = response.get_json()
    assert response.status_code == 400
    assert "buyerId must be a valid UUID" in data["error"] or "orderId must be a valid UUID" in data["error"]


def test_update_order_not_found(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr("app.routes.update_order_db", lambda db, data, b, o: None)

    buyer_id = valid_uuid()
    order_id = valid_uuid()
    
    response = client.put(
        f"/v1/buyer/{buyer_id}/order/{order_id}",
        json={"Quantity": 5},
        headers=API_HEADERS
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Order not found"


def test_update_order_invalid_product(monkeypatch, client):
    def fake_update_order_db(db, data, b, o):
        return {"error": "please provide a valid product_id"}, 400

    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr("app.routes.update_order_db", fake_update_order_db)

    monkeypatch.setattr("app.routes.get_full_order_db", lambda db, b, o: None)
    buyer_id = valid_uuid()
    order_id = valid_uuid()

    payload = {
        "item": {
            "product_id": None,
            "item_name": "Fake",
            "unit_price": 10,
            "quantity": 1
        }
    }

    response = client.put(
        f"/v1/buyer/{buyer_id}/order/{order_id}",
        json=payload,
        headers=API_HEADERS
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "please provide a valid product_id"
