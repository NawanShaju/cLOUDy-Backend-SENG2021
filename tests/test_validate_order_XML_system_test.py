import pytest
from flask import Flask
from app.routes import api

@pytest.fixture
def app():
    test_app = Flask(__name__)
    test_app.register_blueprint(api)
    return test_app

@pytest.fixture
def client(app):
    return app.test_client()

VALID_XML = b"""<?xml version='1.0' encoding='UTF-8'?>
<Order xmlns="urn:oasis:names:specification:ubl:schema:xsd:Order-2"
       xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
       xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
  <cbc:ID>ca21f797-379a-4e27-a703-4992c5ea46fa</cbc:ID>
  <cbc:IssueDate>2026-04-05</cbc:IssueDate>
  <cbc:DocumentCurrencyCode>AUD</cbc:DocumentCurrencyCode>
  <cac:BuyerCustomerParty>
    <cac:Party>
      <cac:PartyIdentification>
        <cbc:ID>70f4810c-5904-454c-8b35-2876e01d9b08</cbc:ID>
      </cac:PartyIdentification>
      <cac:PostalAddress>
        <cbc:StreetName>10 Pitt St</cbc:StreetName>
        <cbc:CityName>Sydney</cbc:CityName>
        <cbc:PostalZone>2000</cbc:PostalZone>
        <cac:Country>
          <cbc:IdentificationCode>AU</cbc:IdentificationCode>
        </cac:Country>
      </cac:PostalAddress>
    </cac:Party>
  </cac:BuyerCustomerParty>
  <cac:SellerSupplierParty>
    <cac:Party>
      <cac:PartyName>
        <cbc:Name>Acme Supplies</cbc:Name>
      </cac:PartyName>
    </cac:Party>
  </cac:SellerSupplierParty>
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">50</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">75.00</cbc:LineExtensionAmount>
      <cac:Price>
        <cbc:PriceAmount currencyID="AUD">1.50</cbc:PriceAmount>
      </cac:Price>
      <cac:Item>
        <cbc:Name>Steel Bolt</cbc:Name>
      </cac:Item>
    </cac:LineItem>
  </cac:OrderLine>
</Order>"""

def test_validate_xml_success(monkeypatch, client):
    monkeypatch.setattr("app.routes.validate_order_xml", lambda xml: (True, []))
    response = client.post("/v1/validate-xml", data=VALID_XML, content_type="application/xml")
    assert response.status_code == 200
    data = response.get_json()
    assert data["valid"] is True
    assert data["errors"] == []

def test_validate_xml_missing_payload(client):
    response = client.post("/v1/validate-xml", data=b"", content_type="application/xml")
    assert response.status_code == 400
    data = response.get_json()
    assert data["valid"] is False
    assert "Missing XML payload" in data["errors"]

def test_validate_xml_invalid_document(monkeypatch, client):
    monkeypatch.setattr(
        "app.routes.validate_order_xml",
        lambda xml: (False, ["Missing required field: <cbc:ID>", "Order must contain at least one <cac:OrderLine>"])
    )
    response = client.post("/v1/validate-xml", data=b"<bad/>", content_type="application/xml")
    assert response.status_code == 400
    data = response.get_json()
    assert data["valid"] is False
    assert len(data["errors"]) == 2

def test_validate_xml_unexpected_exception(monkeypatch, client):
    def raise_exception(xml):
        raise RuntimeError("Something went wrong")
    monkeypatch.setattr("app.routes.validate_order_xml", raise_exception)
    response = client.post("/v1/validate-xml", data=VALID_XML, content_type="application/xml")
    assert response.status_code == 500
    data = response.get_json()
    assert data["valid"] is False
    assert "Something went wrong" in data["errors"]