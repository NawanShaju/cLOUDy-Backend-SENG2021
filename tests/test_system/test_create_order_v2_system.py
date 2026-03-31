import pytest
from flask import Flask
from lxml import etree
from app.routes_v2 import api

API_HEADERS = {"api-key": "dummy-key"}
BUYER_ID = "70f4810c-5904-454c-8b35-2876e01d9b08"
SELLER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"

class DummyDB:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute_query(self, query, params, fetch_all=False):
        return None

    def execute_insert_update_delete(self, query, params):
        return [("f5b163a5-b189-4666-8666-9527705b6ce9",)]


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
def valid_order():
    return {
        "order_date": "2024-01-15",
        "delivery_date": "2024-01-20",
        "currency_code": "AUD",
        "address": {
            "street": "123 Main St",
            "city": "Sydney",
            "state": "NSW",
            "postal_code": "2000",
            "country_code": "AU"
        },
        "items": [
            {
                "item_name": "Widget A",
                "item_description": "A great widget",
                "unit_price": 10.00,
                "quantity": 2
            }
        ]
    }
    
@pytest.fixture
def valid_order_with_seller(valid_order):
    return {**valid_order, "seller_id": SELLER_ID}
    
def _service_result_no_seller():
    return {
        "order_id":    "f5b163a5-b189-4666-8666-9527705b6ce9",
        "buyer_data":  {
            "party_name": "Test Buyer", "address": None,
            "contact": None, "tax_scheme": None,
            "customer_assigned_account_id": None,
            "supplier_assigned_account_id": None,
        },
        "seller_data": None,
    }
    
def _service_result_with_seller():
    return {
        "order_id":    "f5b163a5-b189-4666-8666-9527705b6ce9",
        "buyer_data":  {
            "party_name": "Test Buyer", "address": None,
            "contact": None, "tax_scheme": None,
            "customer_assigned_account_id": None,
            "supplier_assigned_account_id": None,
        },
        "seller_data": {
            "seller_id":                     SELLER_ID,
            "party_name":                    "Consortial Supplies",
            "customer_assigned_account_id":  "CO001",
            "supplier_assigned_account_id":  None,
            "address": {
                "street": "56 Busy Street", "city": "Farthing",
                "state": "NSW", "postal_code": "2000", "country_code": "AU"
            },
            "contact": {
                "name": "Mrs Bouquet", "telephone": "0158 1233714",
                "telefax": None, "email": "bouquet@consortial.com"
            },
            "tax_scheme": None,
        },
    }
    
def test_create_order_v2_invalid_seller_id(client, valid_order):
    valid_order["seller_id"] = "not-a-uuid"
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "seller_id must be a valid UUID"

def test_create_order_v2_invalid_buyer_id(client, valid_order):
    response = client.post(
        "/v2/buyer/not-a-uuid/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "buyerId must be a valid UUID"


def test_create_order_v2_missing_json(client):
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json={},
        headers=API_HEADERS
    )
    assert response.status_code == 400


def test_create_order_v2_missing_address(client, valid_order):
    valid_order.pop("address")
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 400


def test_create_order_v2_missing_items(client, valid_order):
    valid_order.pop("items")
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 400


def test_create_order_v2_buyer_not_found(monkeypatch, client, valid_order):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: ({"error": "Buyer not found"}, 404)
    )
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Buyer not found"
    
def test_create_order_v2_seller_not_found(monkeypatch, client, valid_order_with_seller):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: ({"error": "Seller not found"}, 404)
    )
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order_with_seller,
        headers=API_HEADERS
    )
    assert response.status_code == 404
    assert response.get_json()["error"] == "Seller not found"

def test_create_order_v2_success_status_code(monkeypatch, client, valid_order):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: _service_result_no_seller()
    )
    monkeypatch.setattr("app.routes_v2.xml_to_db", lambda db, xml, order_id: None)
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert response.status_code == 200


def test_create_order_v2_success_returns_xml(monkeypatch, client, valid_order):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: _service_result_no_seller()
    )
    monkeypatch.setattr("app.routes_v2.xml_to_db", lambda db, xml, order_id: None)
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order,
        headers=API_HEADERS
    )
    assert "application/xml" in response.content_type


def test_create_order_v2_success_xml_contains_order_id(monkeypatch, client, valid_order):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: _service_result_no_seller()
    )
    monkeypatch.setattr("app.routes_v2.xml_to_db", lambda db, xml, order_id: None)
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order,
        headers=API_HEADERS
    )
    root = etree.fromstring(response.data)
    assert root.findtext(f"{{{NS_CBC}}}ID") is not None
        
def test_create_order_v2_no_seller_uses_supplier_name(monkeypatch, client, valid_order):
    valid_order["supplier"] = "Fallback Supplier Name"
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: _service_result_no_seller()
    )
    monkeypatch.setattr("app.routes_v2.xml_to_db", lambda db, xml, order_id: None)
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order,
        headers=API_HEADERS
    )
    root = etree.fromstring(response.data)
    path = f"{{{NS_CAC}}}SellerSupplierParty/{{{NS_CAC}}}Party/{{{NS_CAC}}}PartyName/{{{NS_CBC}}}Name"
    assert root.findtext(path) == "Fallback Supplier Name"
    
def test_create_order_v2_with_seller_status_code(monkeypatch, client, valid_order_with_seller):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: _service_result_with_seller()
    )
    monkeypatch.setattr("app.routes_v2.xml_to_db", lambda db, xml, order_id: None)
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order_with_seller,
        headers=API_HEADERS
    )
    assert response.status_code == 200
 
 
def test_create_order_v2_with_seller_returns_xml(monkeypatch, client, valid_order_with_seller):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: _service_result_with_seller()
    )
    monkeypatch.setattr("app.routes_v2.xml_to_db", lambda db, xml, order_id: None)
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order_with_seller,
        headers=API_HEADERS
    )
    assert "application/xml" in response.content_type
 
 
def test_create_order_v2_with_seller_xml_contains_seller_party_name(
    monkeypatch, client, valid_order_with_seller
):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: _service_result_with_seller()
    )
    monkeypatch.setattr("app.routes_v2.xml_to_db", lambda db, xml, order_id: None)
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order_with_seller,
        headers=API_HEADERS
    )
    root = etree.fromstring(response.data)
    path = f"{{{NS_CAC}}}SellerSupplierParty/{{{NS_CAC}}}Party/{{{NS_CAC}}}PartyName/{{{NS_CBC}}}Name"
    assert root.findtext(path) == "Consortial Supplies"
 
 
def test_create_order_v2_with_seller_xml_contains_seller_id(
    monkeypatch, client, valid_order_with_seller
):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: _service_result_with_seller()
    )
    monkeypatch.setattr("app.routes_v2.xml_to_db", lambda db, xml, order_id: None)
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order_with_seller,
        headers=API_HEADERS
    )
    root = etree.fromstring(response.data)
    path = (f"{{{NS_CAC}}}SellerSupplierParty/{{{NS_CAC}}}Party"
            f"/{{{NS_CAC}}}PartyIdentification/{{{NS_CBC}}}ID")
    assert root.findtext(path) == SELLER_ID
 
 
def test_create_order_v2_with_seller_xml_contains_account_id(
    monkeypatch, client, valid_order_with_seller
):
    monkeypatch.setattr("app.routes_v2.PostgresDB", lambda: DummyDB())
    monkeypatch.setattr(
        "app.routes_v2.create_order_v2_service",
        lambda db, data, buyerId: _service_result_with_seller()
    )
    monkeypatch.setattr("app.routes_v2.xml_to_db", lambda db, xml, order_id: None)
    response = client.post(
        f"/v2/buyer/{BUYER_ID}/order",
        json=valid_order_with_seller,
        headers=API_HEADERS
    )
    root = etree.fromstring(response.data)
    path = f"{{{NS_CAC}}}SellerSupplierParty/{{{NS_CBC}}}CustomerAssignedAccountID"
    assert root.findtext(path) == "CO001"