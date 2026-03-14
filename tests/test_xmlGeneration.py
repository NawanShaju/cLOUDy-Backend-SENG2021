import pytest
from lxml import etree
from app.services.xmlGeneration import generate_xml

@pytest.fixture
def valid_data():
    return {
        "order_date": "2024-01-15",
        "delivery_date": "2024-01-20",
        "currency_code": "USD",
        "supplier": "Acme Corp",
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
def parsed_xml(valid_data):
    xml_bytes = generate_xml(valid_data, "order-001", "buyer-001")
    return etree.fromstring(xml_bytes)


# –––––––––––––––––––––––––––––––––––––––––––––––––––– return type ─────────────────────────────────────────────────────

def test_generate_xml_returns_bytes(valid_data):
    result = generate_xml(valid_data, "order-001", "buyer-001")
    assert isinstance(result, bytes)


# –––––––––––––––––––––––––––––––––––––––––––––––––––– top level fields ────────────────────────────────────────────────

def test_generate_xml_order_id(parsed_xml):
    assert parsed_xml.findtext("orderId") == "order-001"


def test_generate_xml_issue_date(parsed_xml):
    assert parsed_xml.findtext("IssueDate") == "2024-01-15"


def test_generate_xml_delivery_date(parsed_xml):
    assert parsed_xml.findtext("DeliveryDate") == "2024-01-20"


def test_generate_xml_currency_code(parsed_xml):
    assert parsed_xml.findtext("CurrencyCode") == "USD"


# –––––––––––––––––––––––––––––––––––––––––––––––––––––– buyer ─────────────────────────────────────────────────────────

def test_generate_xml_buyer_id(parsed_xml):
    assert parsed_xml.findtext("BuyerCustomerParty/ID") == "buyer-001"


def test_generate_xml_buyer_address_street(parsed_xml):
    assert parsed_xml.findtext("BuyerCustomerParty/Address/Street") == "123 Main St"


def test_generate_xml_buyer_address_city(parsed_xml):
    assert parsed_xml.findtext("BuyerCustomerParty/Address/City") == "Sydney"


# –––––––––––––––––––––––––––––––––––––––––––––––––––––– seller ────────────────────────────────────────────────────────

def test_generate_xml_seller_name(parsed_xml):
    assert parsed_xml.findtext("SellerSupplierParty/Name") == "Acme Corp"


# –––––––––––––––––––––––––––––––––––––––––––––––––––––– items ─────────────────────────────────────────────────────────

def test_generate_xml_item_name(parsed_xml):
    assert parsed_xml.findtext("Order/Order/ItemName") == "Widget A"


def test_generate_xml_item_quantity(parsed_xml):
    assert parsed_xml.findtext("Order/Order/Quantity") == "2"


def test_generate_xml_item_price(parsed_xml):
    assert parsed_xml.findtext("Order/Order/Price") == "10.0"


def test_generate_xml_item_description(parsed_xml):
    assert parsed_xml.findtext("Order/Order/ItemDescription") == "A great widget"


def test_generate_xml_item_description_omitted_when_missing(valid_data):
    valid_data["items"][0].pop("item_description")
    xml_bytes = generate_xml(valid_data, "order-001", "buyer-001")
    root = etree.fromstring(xml_bytes)
    assert root.find("Order/Order/ItemDescription") is None


def test_generate_xml_single_item_as_dict(valid_data):
    valid_data["items"] = {"item_name": "Widget A", "unit_price": 10.00, "quantity": 2}
    xml_bytes = generate_xml(valid_data, "order-001", "buyer-001")
    root = etree.fromstring(xml_bytes)
    assert root.findtext("Order/Order/ItemName") == "Widget A"