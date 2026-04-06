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
        return [("seller-uuid-1234",)]


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


def test_delete_seller_invalid_seller_id(client):
    response = client.delete(
        "/v1/seller/not-a-uuid",
        headers=API_HEADERS
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "sellerId must be a valid UUID"


def test_delete_seller_not_found(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_seller_service",
        lambda db, seller_id: ({"error": "Seller not found"}, 404)
    )

    response = client.delete(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Seller not found"


def test_delete_seller_fails_when_orders_still_exist(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_seller_service",
        lambda db, seller_id: (
            {
                "error": "Seller cannot be deleted because related orders still exist. All related orders must be hard deleted first."
            },
            409
        )
    )

    response = client.delete(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )
    assert response.status_code == 409
    assert "hard deleted first" in response.get_json()["error"]


def test_delete_seller_success_status_code(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_seller_service",
        lambda db, seller_id: {
            "seller_id": seller_id,
            "message": "Seller deleted successfully"
        }
    )

    response = client.delete(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )
    assert response.status_code == 200


def test_delete_seller_success_returns_seller_id(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_seller_service",
        lambda db, seller_id: {
            "seller_id": seller_id,
            "message": "Seller deleted successfully"
        }
    )

    response = client.delete(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )
    assert response.get_json()["sellerId"] == "70f4810c-5904-454c-8b35-2876e01d9b08"


def test_delete_seller_success_returns_message(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.delete_seller_service",
        lambda db, seller_id: {
            "seller_id": seller_id,
            "message": "Seller deleted successfully"
        }
    )

    response = client.delete(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        headers=API_HEADERS
    )
    assert response.get_json()["message"] == "Seller deleted successfully"