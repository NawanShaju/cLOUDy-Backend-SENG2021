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
        return [(
            params["order_id"],     # order_id
            params["buyer_id"],     # external_buyer_id
            "x",                    # filler
            "x",
            "x",
            "x",
            "CANCELED"              # status
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


def test_delete_order_success(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())

    buyer_id = valid_uuid()
    order_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/{order_id}",
        headers=API_HEADERS
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["orderId"] == order_id
    assert "deleted successfully" in data["message"]


def test_delete_order_not_found(monkeypatch, client):
    class NotFoundDB(DummyDB):
        def execute_query(self, query, params, fetch_all=False):
            return None

    monkeypatch.setattr("app.routes.PostgresDB", lambda: NotFoundDB())

    buyer_id = valid_uuid()
    order_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/{order_id}",
        headers=API_HEADERS
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "Order not found"


def test_delete_order_forbidden(monkeypatch, client):
    class ForbiddenDB(DummyDB):
        def execute_query(self, query, params, fetch_all=False):
            return [(
                params["order_id"],
                "different-buyer",
                "x",
                "x",
                "x",
                "x",
                "CANCELED"
            )]

    monkeypatch.setattr("app.routes.PostgresDB", lambda: ForbiddenDB())

    buyer_id = valid_uuid()
    order_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/{order_id}",
        headers=API_HEADERS
    )

    assert response.status_code == 403
    data = response.get_json()
    assert "Forbidden" in data["error"]


def test_delete_order_not_canceled(monkeypatch, client):
    class NotCanceledDB(DummyDB):
        def execute_query(self, query, params, fetch_all=False):
            return [(
                params["order_id"],
                params["buyer_id"],
                "x",
                "x",
                "x",
                "x",
                "CREATED"
            )]

    monkeypatch.setattr("app.routes.PostgresDB", lambda: NotCanceledDB())

    buyer_id = valid_uuid()
    order_id = valid_uuid()

    response = client.delete(
        f"/v1/buyer/{buyer_id}/order/{order_id}",
        headers=API_HEADERS
    )

    assert response.status_code == 409
    data = response.get_json()
    assert data["error"] == "Order cannot be deleted unless status is CANCELED"