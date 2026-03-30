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
        return [("new-buyer-uuid-1234",)]


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
def valid_buyer():
    return {
        "party_name": "IYT Corporation",
        "customer_assigned_account_id": "XFB01",
        "supplier_assigned_account_id": "GT00978567",
        "address": {
            "street": "10 Pitt St",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000",
            "country_code": "AU"
        },
        "contact": {
            "name": "Fred Churchill",
            "telephone": "0127 2653214",
            "telefax": "0127 2653215",
            "email": "fred@iytcorp.com"
        },
        "tax_scheme": {
            "registration_name": "IYT Corp Tax",
            "company_id": "12356478",
            "exemption_reason": "Local Authority",
            "scheme_id": "VAT",
            "tax_type_code": "VAT"
        }
    }

def test_create_buyer_missing_json(client):
    response = client.post("/v1/buyer", json={}, headers=API_HEADERS)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid Json Provided"


def test_create_buyer_missing_party_name(monkeypatch, client, valid_buyer):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    valid_buyer.pop("party_name")
    response = client.post("/v1/buyer", json=valid_buyer, headers=API_HEADERS)
    assert response.status_code == 400
    assert response.get_json()["error"] == "party_name is required"


def test_create_buyer_missing_account_id(monkeypatch, client, valid_buyer):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    valid_buyer.pop("customer_assigned_account_id")
    response = client.post("/v1/buyer", json=valid_buyer, headers=API_HEADERS)
    assert response.status_code == 400
    assert response.get_json()["error"] == "customer_assigned_account_id is required"


def test_create_buyer_duplicate_account_id(monkeypatch, client, valid_buyer):
    monkeypatch.setattr(
        "app.routes.PostgresDB",
        lambda: DummyDB()
    )
    monkeypatch.setattr(
        "app.routes.create_buyer_service",
        lambda db, data: ({"error": "A buyer with this customer_assigned_account_id already exists"}, 409)
    )
    response = client.post("/v1/buyer", json=valid_buyer, headers=API_HEADERS)
    assert response.status_code == 409
    assert "already exists" in response.get_json()["error"]


def test_create_buyer_success_status_code(monkeypatch, client, valid_buyer):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.create_buyer_service",
        lambda db, data: {"buyer_id": "new-buyer-uuid-1234"}
    )
    response = client.post("/v1/buyer", json=valid_buyer, headers=API_HEADERS)
    assert response.status_code == 201


def test_create_buyer_success_returns_buyer_id(monkeypatch, client, valid_buyer):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.create_buyer_service",
        lambda db, data: {"buyer_id": "new-buyer-uuid-1234"}
    )
    response = client.post("/v1/buyer", json=valid_buyer, headers=API_HEADERS)
    data = response.get_json()
    assert data["buyerId"] == "new-buyer-uuid-1234"


def test_create_buyer_success_returns_message(monkeypatch, client, valid_buyer):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.create_buyer_service",
        lambda db, data: {"buyer_id": "new-buyer-uuid-1234"}
    )
    response = client.post("/v1/buyer", json=valid_buyer, headers=API_HEADERS)
    assert response.get_json()["message"] == "Buyer created successfully"


def test_create_buyer_minimal_payload(monkeypatch, client):
    """Buyer with only required fields (no address, contact, or tax_scheme)."""
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes.create_buyer_service",
        lambda db, data: {"buyer_id": "minimal-buyer-id"}
    )
    response = client.post(
        "/v1/buyer",
        json={"party_name": "Minimal Corp", "customer_assigned_account_id": "MIN01"},
        headers=API_HEADERS
    )
    assert response.status_code == 201
    assert response.get_json()["buyerId"] == "minimal-buyer-id"