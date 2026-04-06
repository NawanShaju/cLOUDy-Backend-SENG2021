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


@pytest.fixture
def valid_update_seller_payload():
    return {
        "party_name": "Updated Seller Pty Ltd",
        "supplier_assigned_account_id": "SUP-NEW-001",
        "address": {
            "street": "20 George St",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000",
            "country_code": "AU"
        },
        "contact": {
            "name": "Updated Seller Contact",
            "telephone": "0400000000",
            "telefax": "0299999999",
            "email": "updated@seller.com"
        },
        "tax_scheme": {
            "registration_name": "Updated Seller Tax Name",
            "company_id": "999999",
            "exemption_reason": "None",
            "scheme_id": "GST",
            "tax_type_code": "GST"
        }
    }


def test_update_seller_missing_json(client):
    response = client.put(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        json={},
        headers=API_HEADERS
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid Json Provided"


def test_update_seller_invalid_seller_id(client, valid_update_seller_payload):
    response = client.put(
        "/v1/seller/not-a-uuid",
        json=valid_update_seller_payload,
        headers=API_HEADERS
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "sellerId must be a valid UUID"


def test_update_seller_not_found(monkeypatch, client, valid_update_seller_payload):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.update_seller_service",
        lambda db, seller_id, data: ({"error": "Seller not found"}, 404)
    )

    response = client.put(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        json=valid_update_seller_payload,
        headers=API_HEADERS
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Seller not found"


def test_update_seller_empty_body(monkeypatch, client, valid_update_seller_payload):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.update_seller_service",
        lambda db, seller_id, data: (
            {"error": "Request body cannot be empty"}, 400
        )
    )

    response = client.put(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        json=valid_update_seller_payload,
        headers=API_HEADERS
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Request body cannot be empty"


def test_update_seller_success_status_code(monkeypatch, client, valid_update_seller_payload):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.update_seller_service",
        lambda db, seller_id, data: {
            "seller_id": seller_id,
            "message": "Seller updated successfully"
        }
    )

    response = client.put(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        json=valid_update_seller_payload,
        headers=API_HEADERS
    )
    assert response.status_code == 200


def test_update_seller_success_returns_seller_id(monkeypatch, client, valid_update_seller_payload):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.update_seller_service",
        lambda db, seller_id, data: {
            "seller_id": seller_id,
            "message": "Seller updated successfully"
        }
    )

    response = client.put(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        json=valid_update_seller_payload,
        headers=API_HEADERS
    )
    assert response.get_json()["sellerId"] == "70f4810c-5904-454c-8b35-2876e01d9b08"


def test_update_seller_success_returns_message(monkeypatch, client, valid_update_seller_payload):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.update_seller_service",
        lambda db, seller_id, data: {
            "seller_id": seller_id,
            "message": "Seller updated successfully"
        }
    )

    response = client.put(
        "/v1/seller/70f4810c-5904-454c-8b35-2876e01d9b08",
        json=valid_update_seller_payload,
        headers=API_HEADERS
    )
    assert response.get_json()["message"] == "Seller updated successfully"