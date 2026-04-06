import pytest
from flask import Flask
from app.routes import api

API_HEADERS = {"api-key": "dummy-key"}


class DummyDB:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute_query(self, query, params, fetch_all=False):
        return None

    def execute_insert_update_delete(self, query, params):
        return [("buyer-uuid-1234",)]


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


def test_delete_buyer_invalid_buyer_id(client):
    response = client.delete(
        "/v1/buyer/not-a-uuid",
        headers=API_HEADERS
    )
    assert response.status_code == 400


def test_delete_buyer_not_found(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_buyer_service",
        lambda db, buyer_id, api_key: ({"error": "Buyer not found"}, 404)
    )

    response = client.delete(
        "/v1/buyer/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )

    assert response.status_code == 404


def test_delete_buyer_forbidden(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_buyer_service",
        lambda db, buyer_id, api_key: (
            {"error": "You are not authorised to delete this buyer"}, 403
        )
    )

    response = client.delete(
        "/v1/buyer/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )

    assert response.status_code == 403


def test_delete_buyer_fails_when_orders_still_exist(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_buyer_service",
        lambda db, buyer_id, api_key: (
            {"error": "Buyer cannot be deleted because related orders still exist. All related orders must be hard deleted first."},
            409
        )
    )

    response = client.delete(
        "/v1/buyer/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )

    assert response.status_code == 409


def test_delete_buyer_success_status_code(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_buyer_service",
        lambda db, buyer_id, api_key: {
            "buyer_id": buyer_id,
            "message": "Buyer deleted successfully"
        }
    )

    response = client.delete(
        "/v1/buyer/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )

    assert response.status_code == 200


def test_delete_buyer_success_returns_buyer_id(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_buyer_service",
        lambda db, buyer_id, api_key: {
            "buyer_id": buyer_id,
            "message": "Buyer deleted successfully"
        }
    )

    response = client.delete(
        "/v1/buyer/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )

    assert response.get_json()["buyerId"] == "70f4810c-5904-454c-8b35-2876e01d9b08"


def test_delete_buyer_success_returns_message(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_buyer_service",
        lambda db, buyer_id, api_key: {
            "buyer_id": buyer_id,
            "message": "Buyer deleted successfully"
        }
    )

    response = client.delete(
        "/v1/buyer/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )

    assert response.get_json()["message"] == "Buyer deleted successfully"