import pytest
from lxml import etree
from app.services.xml_generation import generate_xml

NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

def cbc(tag):
    return f"{{{NS_CBC}}}{tag}"

def cac(tag):
    return f"{{{NS_CAC}}}{tag}"

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


# ––––––––––––––––––––––––––––––––––––––––––– return type ──────────────────────────────────────────────────────────────

def test_generate_xml_returns_bytes(valid_data):
    result = generate_xml(valid_data, "order-001", "buyer-001")
    assert isinstance(result, bytes)


# ––––––––––––––––––––––––––––––––––––––––––– top level fields ─────────────────────────────────────────────────────────

def test_generate_xml_order_id(parsed_xml):
    assert parsed_xml.findtext(cbc("ID")) == "order-001"


def test_generate_xml_issue_date(parsed_xml):
    assert parsed_xml.findtext(cbc("IssueDate")) == "2024-01-15"


def test_generate_xml_currency_code(parsed_xml):
    assert parsed_xml.findtext(cbc("DocumentCurrencyCode")) == "USD"


def test_generate_xml_ubl_version(parsed_xml):
    assert parsed_xml.findtext(cbc("UBLVersionID")) == "2.1"


# ––––––––––––––––––––––––––––––––––––––––––––– delivery date ──────────────────────────────────────────────────────────

def test_generate_xml_delivery_date(parsed_xml):
    path = f"{cac('Delivery')}/{cac('RequestedDeliveryPeriod')}/{cbc('EndDate')}"
    assert parsed_xml.findtext(path) == "2024-01-20"


# ––––––––––––––––––––––––––––––––––––––––––––––––– buyer ──────────────────────────────────────────────────────────────

def test_generate_xml_buyer_id(parsed_xml):
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PartyIdentification')}/{cbc('ID')}"
    assert parsed_xml.findtext(path) == "buyer-001"


def test_generate_xml_buyer_address_street(parsed_xml):
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PostalAddress')}/{cbc('StreetName')}"
    assert parsed_xml.findtext(path) == "123 Main St"


def test_generate_xml_buyer_address_city(parsed_xml):
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PostalAddress')}/{cbc('CityName')}"
    assert parsed_xml.findtext(path) == "Sydney"


def test_generate_xml_buyer_address_country(parsed_xml):
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PostalAddress')}/{cac('Country')}/{cbc('IdentificationCode')}"
    assert parsed_xml.findtext(path) == "AU"


# –––––––––––––––––––––––––––––––––––––––––––––––– seller ──────────────────────────────────────────────────────────────

def test_generate_xml_seller_name(parsed_xml):
    path = f"{cac('SellerSupplierParty')}/{cac('Party')}/{cac('PartyName')}/{cbc('Name')}"
    assert parsed_xml.findtext(path) == "Acme Corp"


# ––––––––––––––––––––––––––––––––––––––––––––– monetary total ─────────────────────────────────────────────────────────

def test_generate_xml_total_amount(parsed_xml):
    path = f"{cac('AnticipatedMonetaryTotal')}/{cbc('PayableAmount')}"
    assert parsed_xml.findtext(path) == "20.00"


def test_generate_xml_line_extension_amount(parsed_xml):
    path = f"{cac('AnticipatedMonetaryTotal')}/{cbc('LineExtensionAmount')}"
    assert parsed_xml.findtext(path) == "20.00"


# –––––––––––––––––––––––––––––––––––––––––––––––– items ───────────────────────────────────────────────────────────────

def test_generate_xml_item_name(parsed_xml):
    path = f"{cac('OrderLine')}/{cac('LineItem')}/{cac('Item')}/{cbc('Name')}"
    assert parsed_xml.findtext(path) == "Widget A"
    
    
def test_generate_xml_item_product_id(valid_data):
    valid_data["items"][0]["product_id"] = "prod-123"
    xml_bytes = generate_xml(valid_data, "order-001", "buyer-001")
    root = etree.fromstring(xml_bytes)
    path = f"{cac('OrderLine')}/{cac('LineItem')}/{cac('Item')}/{cac('SellersItemIdentification')}/{cbc('ID')}"
    assert root.findtext(path) == "prod-123"


def test_generate_xml_item_quantity(parsed_xml):
    path = f"{cac('OrderLine')}/{cac('LineItem')}/{cbc('Quantity')}"
    assert parsed_xml.findtext(path) == "2"


def test_generate_xml_item_price(parsed_xml):
    path = f"{cac('OrderLine')}/{cac('LineItem')}/{cac('Price')}/{cbc('PriceAmount')}"
    assert parsed_xml.findtext(path) == "10.00"


def test_generate_xml_item_description(parsed_xml):
    path = f"{cac('OrderLine')}/{cac('LineItem')}/{cac('Item')}/{cbc('Description')}"
    assert parsed_xml.findtext(path) == "A great widget"


def test_generate_xml_item_description_omitted_when_missing(valid_data):
    valid_data["items"][0].pop("item_description")
    xml_bytes = generate_xml(valid_data, "order-001", "buyer-001")
    root = etree.fromstring(xml_bytes)
    path = f"{cac('OrderLine')}/{cac('LineItem')}/{cac('Item')}/{cbc('Description')}"
    assert root.find(path) is None


def test_generate_xml_single_item_as_dict(valid_data):
    valid_data["items"] = {"item_name": "Widget A", "unit_price": 10.00, "quantity": 2}
    xml_bytes = generate_xml(valid_data, "order-001", "buyer-001")
    root = etree.fromstring(xml_bytes)
    path = f"{cac('OrderLine')}/{cac('LineItem')}/{cac('Item')}/{cbc('Name')}"
    assert root.findtext(path) == "Widget A"