import pytest
from flask import Flask
from app.routes import api

class DummyDB:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    def execute_query(self, query, params):
        return None
    def execute_insert_update_delete(self, query, params):
        return None

@pytest.fixture
def app():
    test_app = Flask(__name__)
    test_app.register_blueprint(api)
    return test_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_apiKey_success(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr("app.routes.get_api_key", lambda db, u, p: "dummy-apikey-1234")
    
    response = client.post(
        "/get-key",
        json={"username": "test", "password": "test123"}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["apikey"] == "dummy-apikey-1234"

def test_create_apiKey_missing_json(client):
    response = response = client.post("/get-key", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Invalid json Provided"

def test_create_apiKey_value_error(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    
    def raise_value_error(db, u, p):
        raise ValueError("Invalid credentials")
    
    monkeypatch.setattr("app.routes.get_api_key", raise_value_error)
    
    response = client.post("/get-key", json={"username": "test", "password": "wrong"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "Invalid credentials"

def test_create_apiKey_permission_error(monkeypatch, client):
    monkeypatch.setattr("app.routes.PostgresDB", lambda: DummyDB())
    
    def raise_permission_error(db, u, p):
        raise PermissionError("Unauthorized")
    
    monkeypatch.setattr("app.routes.get_api_key", raise_permission_error)
    
    response = client.post("/get-key", json={"username": "test", "password": "test123"})
    assert response.status_code == 401
    data = response.get_json()
    assert data["error"] == "Unauthorized"