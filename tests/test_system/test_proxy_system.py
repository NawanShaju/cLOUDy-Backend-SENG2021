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

class TestProxyRoute:
 
    def test_missing_body_returns_400(self, client):
        response = client.post("/v1/proxy", json={}, headers=API_HEADERS)
        assert response.status_code == 400
        assert response.get_json()["error"] == "Request body is required"
 
    def test_missing_url_returns_400(self, client):
        response = client.post(
            "/v1/proxy",
            json={"method": "GET"},
            headers=API_HEADERS
        )
        assert response.status_code == 400
        assert response.get_json()["error"] == "url is required"
 
    def test_successful_json_body_request(self, client):
        mock_response = MagicMock()
        mock_response.content = b'{"result": "ok"}'
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
 
        with patch("app.proxy_route.requests.request", return_value=mock_response):
            response = client.post(
                "/v1/proxy",
                json={
                    "url": "https://example.com/api/resource",
                    "method": "POST",
                    "headers": {"X-API-KEY": "their-key"},
                    "body": {"key": "value"}
                },
                headers=API_HEADERS
            )
        assert response.status_code == 200
        assert response.get_json() == {"result": "ok"}
 
    def test_successful_string_body_request(self, client):
        mock_response = MagicMock()
        mock_response.content = b'{"result": "ok"}'
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
 
        with patch("app.proxy_route.requests.request", return_value=mock_response) as mock_req:
            response = client.post(
                "/v1/proxy",
                json={
                    "url": "https://example.com/api/xml",
                    "method": "POST",
                    "headers": {"Content-Type": "application/xml"},
                    "body": "<Order><ID>1</ID></Order>"
                },
                headers=API_HEADERS
            )
        assert response.status_code == 200
        # String body should be sent as data=, not json=
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["data"] == "<Order><ID>1</ID></Order>"
        assert call_kwargs["json"] is None
 
    def test_default_method_is_get(self, client):
        mock_response = MagicMock()
        mock_response.content = b'{}'
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
 
        with patch("app.proxy_route.requests.request", return_value=mock_response) as mock_req:
            client.post(
                "/v1/proxy",
                json={"url": "https://example.com/api"},
                headers=API_HEADERS
            )
        assert mock_req.call_args[1]["method"] == "GET"
 
    def test_params_forwarded(self, client):
        mock_response = MagicMock()
        mock_response.content = b'{}'
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
 
        with patch("app.proxy_route.requests.request", return_value=mock_response) as mock_req:
            client.post(
                "/v1/proxy",
                json={
                    "url": "https://example.com/api",
                    "method": "GET",
                    "params": {"limit": 10, "offset": 0}
                },
                headers=API_HEADERS
            )
        assert mock_req.call_args[1]["params"] == {"limit": 10, "offset": 0}
 
    def test_headers_forwarded(self, client):
        mock_response = MagicMock()
        mock_response.content = b'{}'
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
 
        with patch("app.proxy_route.requests.request", return_value=mock_response) as mock_req:
            client.post(
                "/v1/proxy",
                json={
                    "url": "https://example.com/api",
                    "headers": {"X-API-KEY": "their-secret", "Accept": "application/json"}
                },
                headers=API_HEADERS
            )
        forwarded = mock_req.call_args[1]["headers"]
        assert forwarded["X-API-KEY"] == "their-secret"
        assert forwarded["Accept"] == "application/json"
 
    def test_proxies_non_200_status_code(self, client):
        mock_response = MagicMock()
        mock_response.content = b'{"error": "not found"}'
        mock_response.status_code = 404
        mock_response.headers = {"Content-Type": "application/json"}
 
        with patch("app.proxy_route.requests.request", return_value=mock_response):
            response = client.post(
                "/v1/proxy",
                json={"url": "https://example.com/missing"},
                headers=API_HEADERS
            )
        assert response.status_code == 404
 
    def test_timeout_returns_504(self, client):
        import requests as req_lib
        with patch("app.proxy_route.requests.request",
                   side_effect=req_lib.exceptions.Timeout):
            response = client.post(
                "/v1/proxy",
                json={"url": "https://example.com/slow"},
                headers=API_HEADERS
            )
        assert response.status_code == 504
        assert "timed out" in response.get_json()["error"]
 
    def test_connection_error_returns_502(self, client):
        import requests as req_lib
        with patch("app.proxy_route.requests.request",
                   side_effect=req_lib.exceptions.ConnectionError):
            response = client.post(
                "/v1/proxy",
                json={"url": "https://unreachable.example.com"},
                headers=API_HEADERS
            )
        assert response.status_code == 502
        assert "Could not connect" in response.get_json()["error"]
 
    def test_unexpected_exception_returns_500(self, client):
        with patch("app.proxy_route.requests.request",
                   side_effect=Exception("something broke")):
            response = client.post(
                "/v1/proxy",
                json={"url": "https://example.com"},
                headers=API_HEADERS
            )
        assert response.status_code == 500
        assert "something broke" in response.get_json()["error"]