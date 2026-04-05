import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from app.routes import api
from app.proxy_route import proxy
 
API_HEADERS = {"api-key": "dummy-key"}
 
@pytest.fixture
def app():
    test_app = Flask(__name__)
    test_app.register_blueprint(api)
    test_app.register_blueprint(proxy)
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

class DummySellersDB:
    def __enter__(self):
        return self
 
    def __exit__(self, *a):
        pass
 
    def execute_query(self, query, params=None, fetch_all=False):
        return [
            ("6ca72a7f-ad4a-4a55-a292-f44b109fa9b2", "Consortial Supplies", "CO001"),
            ("b2c3d4e5-f6a7-8901-bcde-f12345678901", "Acme Supplies", "CO002"),
        ]
 
    def execute_insert_update_delete(self, query, params):
        return None
 
 
class EmptySellersDB:
    def __enter__(self):
        return self
 
    def __exit__(self, *a):
        pass
 
    def execute_query(self, query, params=None, fetch_all=False):
        return []
 
    def execute_insert_update_delete(self, query, params):
        return None
 
 
class TestGetAllSellers:
 
    def test_returns_200(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: DummySellersDB())
        response = client.get("/v1/sellers", headers=API_HEADERS)
        assert response.status_code == 200
 
    def test_returns_sellers_list(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: DummySellersDB())
        response = client.get("/v1/sellers", headers=API_HEADERS)
        data = response.get_json()
        assert "sellers" in data
        assert len(data["sellers"]) == 2
 
    def test_seller_fields_mapped_correctly(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: DummySellersDB())
        response = client.get("/v1/sellers", headers=API_HEADERS)
        seller = response.get_json()["sellers"][0]
        assert seller["seller_id"] == "6ca72a7f-ad4a-4a55-a292-f44b109fa9b2"
        assert seller["party_name"] == "Consortial Supplies"
        assert seller["customer_assigned_account_id"] == "CO001"
 
    def test_empty_sellers_returns_empty_list(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: EmptySellersDB())
        response = client.get("/v1/sellers", headers=API_HEADERS)
        assert response.status_code == 200
        assert response.get_json() == {"sellers": []}
 
class TestCreateSeller:
 
    def test_missing_json_returns_400(self, client):
        response = client.post("/v1/seller", json={}, headers=API_HEADERS)
        assert response.status_code == 400
        assert response.get_json()["error"] == "Invalid Json Provided"
 
    def test_missing_party_name_returns_400(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: DummySellersDB())
        monkeypatch.setattr(
            "app.routes.create_seller_service",
            lambda db, data: ({"error": "party_name is required"}, 400)
        )
        response = client.post(
            "/v1/seller",
            json={"customer_assigned_account_id": "CO001"},
            headers=API_HEADERS
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "party_name is required"
 
    def test_missing_account_id_returns_400(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: DummySellersDB())
        monkeypatch.setattr(
            "app.routes.create_seller_service",
            lambda db, data: ({"error": "customer_assigned_account_id is required"}, 400)
        )
        response = client.post(
            "/v1/seller",
            json={"party_name": "Consortial Supplies"},
            headers=API_HEADERS
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "customer_assigned_account_id is required"
 
    def test_duplicate_account_id_returns_409(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: DummySellersDB())
        monkeypatch.setattr(
            "app.routes.create_seller_service",
            lambda db, data: ({"error": "A seller with this customer_assigned_account_id already exists"}, 409)
        )
        response = client.post(
            "/v1/seller",
            json={"party_name": "Consortial Supplies", "customer_assigned_account_id": "CO001"},
            headers=API_HEADERS
        )
        assert response.status_code == 409
        assert "already exists" in response.get_json()["error"]
 
    def test_success_returns_201(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: DummySellersDB())
        monkeypatch.setattr(
            "app.routes.create_seller_service",
            lambda db, data: {"seller_id": "6ca72a7f-ad4a-4a55-a292-f44b109fa9b2"}
        )
        response = client.post(
            "/v1/seller",
            json={"party_name": "Consortial Supplies", "customer_assigned_account_id": "CO003"},
            headers=API_HEADERS
        )
        assert response.status_code == 201
 
    def test_success_returns_seller_id(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: DummySellersDB())
        monkeypatch.setattr(
            "app.routes.create_seller_service",
            lambda db, data: {"seller_id": "6ca72a7f-ad4a-4a55-a292-f44b109fa9b2"}
        )
        response = client.post(
            "/v1/seller",
            json={"party_name": "Consortial Supplies", "customer_assigned_account_id": "CO003"},
            headers=API_HEADERS
        )
        data = response.get_json()
        assert data["sellerId"] == "6ca72a7f-ad4a-4a55-a292-f44b109fa9b2"
 
    def test_success_returns_message(self, monkeypatch, client):
        monkeypatch.setattr("app.routes.PostgresDB", lambda: DummySellersDB())
        monkeypatch.setattr(
            "app.routes.create_seller_service",
            lambda db, data: {"seller_id": "6ca72a7f-ad4a-4a55-a292-f44b109fa9b2"}
        )
        response = client.post(
            "/v1/seller",
            json={"party_name": "Consortial Supplies", "customer_assigned_account_id": "CO003"},
            headers=API_HEADERS
        )
        assert response.get_json()["message"] == "Seller created successfully"
