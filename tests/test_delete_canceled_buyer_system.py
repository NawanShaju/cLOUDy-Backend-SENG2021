import pytest
from flask import Flask
from app.routes import api
import uuid 

API_HEADERS = {"api-key": "dummy-key"}

class DummyDB:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def execute_query(self, query, params, fetch_all=False):
        if "status = 'CANCELED'" in query:
            return [("order1",)]
        return [("buyer-exists",)]
    def execute_insert_update_delete(self, query, params):
        return True


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


def test_delete_cancelled_orders(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())

    buyer_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/CANCELED",
        headers=API_HEADERS
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["buyerId"] == buyer_id
    assert "deleted successfully" in data["message"]


def test_delete_cancelled_orders_invalid(client):
    response = client.delete(
        "/v1/buyer/invalid-uuid/order/CANCELED",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "buyerId must be a valid UUID" in data["error"]


def test_delete_cancelled_orders_not_found(monkeypatch, client):
    class EmptyDB(DummyDB):
        def execute_query(self, query, params, fetch_all=False):
            if "external_buyer_id" in query:
                return None
            return []

    monkeypatch.setattr("app.routes.PostgresDB", lambda: EmptyDB())

    buyer_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/CANCELED",
        headers=API_HEADERS
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Buyer not found"


def test_delete_cancelled_orders_none(monkeypatch, client):
    class NoCancelledDB(DummyDB):
        def execute_query(self, query, params, fetch_all=False):
            if "status = 'CANCELED'" in query:
                return []
            return [("buyer-exists",)]

    monkeypatch.setattr("app.routes.PostgresDB", lambda: NoCancelledDB())

    buyer_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/CANCELED",
        headers=API_HEADERS
    )

    assert response.status_code == 409
    data = response.get_json()
    assert "No canceled orders found" in data["error"]