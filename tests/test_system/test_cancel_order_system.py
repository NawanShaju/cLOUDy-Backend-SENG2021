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
    def execute_query(self, query, params, fetch_all=False):  # add fetch_all
        return [(
            "order1",
            params["buyer_id"],
            None,
            None,
            None,
            None,
            "CREATED"
        )]
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

    monkeypatch.setattr("app.services.api_key.PostgresDB", lambda: FakeAuthDB())


def valid_uuid():
    return str(uuid.uuid4())


def test_cancel_order_success(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())

    buyer_id = valid_uuid()
    order_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/{order_id}/CANCELED",
        headers=API_HEADERS
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "CANCELED"
    assert data["orderId"] == order_id


def test_cancel_order_invalid_order_id(client):
    buyer_id = valid_uuid()
    response = client.delete(
        "/v1/buyer/buyer_id/order/invalid-uuid/CANCELED",
        headers=API_HEADERS
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "orderId must be a valid UUID" in data["error"]


def test_cancel_order_not_found(monkeypatch, client):
    class EmptyDB(DummyDB):
        def execute_query(self, query, params, fetch_all=False):
            return None

    monkeypatch.setattr("app.routes.PostgresDB", lambda: EmptyDB())

    buyer_id = valid_uuid()
    order_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/{order_id}/CANCELED",
        headers=API_HEADERS
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Order not found"


def test_cancel_order_forbidden(monkeypatch, client):
    class WrongBuyerDB(DummyDB):
        def execute_query(self, query, params, fetch_all=False):  # add fetch_all
            return [(
                "order1",
                "different-buyer",
                None,
                None,
                None,
                None,
                "CREATED"
            )]

    monkeypatch.setattr("app.routes.PostgresDB", lambda: WrongBuyerDB())

    buyer_id = valid_uuid()
    order_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/{order_id}/CANCELED",
        headers=API_HEADERS
    )

    assert response.status_code == 403
    data = response.get_json()
    assert "Forbidden" in data["error"]


def test_cancel_order_conflict(monkeypatch, client):
    class CancelledDB(DummyDB):
        def execute_query(self, query, params, fetch_all=False):
            return [(
                "order1",
                params["buyer_id"],
                None,
                None,
                None,
                None,
                "CANCELED"
            )]

    monkeypatch.setattr("app.routes.PostgresDB", lambda: CancelledDB())

    buyer_id = valid_uuid()
    order_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/{order_id}/CANCELED",
        headers=API_HEADERS
    )

    assert response.status_code == 409
    data = response.get_json()
    assert "cannot be canceled" in data["error"]