import pytest
from lxml import etree
from app.utils.xml_generation import generate_xml_v2

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
        "currency_code": "AUD",
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
def full_buyer_data():
    return {
        "party_name": "IYT Corporation",
        "customer_assigned_account_id": "XFB01",
        "supplier_assigned_account_id": "GT00978567",
        "address": {
            "street": "56A Avon Way",
            "city": "Bridgtow",
            "state": "Avon",
            "postal_code": "ZZ99 1ZZ",
            "country_code": "GB"
        },
        "tax_scheme": {
            "registration_name": "Bridgtow District Council",
            "company_id": "12356478",
            "exemption_reason": "Local Authority",
            "scheme_id": "UK VAT",
            "tax_type_code": "VAT"
        },
        "contact": {
            "name": "Mr Fred Churchill",
            "telephone": "0127 2653214",
            "telefax": "0127 2653215",
            "email": "fred@iytcorporation.gov.uk"
        }
    }


@pytest.fixture
def minimal_buyer_data():
    """Buyer with no optional fields — tests that absent fields produce no elements."""
    return {
        "party_name": None,
        "customer_assigned_account_id": None,
        "supplier_assigned_account_id": None,
        "address": None,
        "tax_scheme": None,
        "contact": None
    }


@pytest.fixture
def parsed_xml_v2(valid_data, full_buyer_data):
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", full_buyer_data)
    return etree.fromstring(xml_bytes)


def test_generate_xml_v2_returns_bytes(valid_data, full_buyer_data):
    result = generate_xml_v2(valid_data, "order-001", "buyer-001", full_buyer_data)
    assert isinstance(result, bytes)


def test_generate_xml_v2_customer_assigned_account_id(parsed_xml_v2):
    path = f"{cac('BuyerCustomerParty')}/{cbc('CustomerAssignedAccountID')}"
    assert parsed_xml_v2.findtext(path) == "XFB01"


def test_generate_xml_v2_supplier_assigned_account_id(parsed_xml_v2):
    path = f"{cac('BuyerCustomerParty')}/{cbc('SupplierAssignedAccountID')}"
    assert parsed_xml_v2.findtext(path) == "GT00978567"


def test_generate_xml_v2_customer_account_id_omitted_when_absent(valid_data, minimal_buyer_data):
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", minimal_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('BuyerCustomerParty')}/{cbc('CustomerAssignedAccountID')}"
    assert root.find(path) is None


def test_generate_xml_v2_supplier_account_id_omitted_when_absent(valid_data, minimal_buyer_data):
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", minimal_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('BuyerCustomerParty')}/{cbc('SupplierAssignedAccountID')}"
    assert root.find(path) is None


def test_generate_xml_v2_buyer_party_name(parsed_xml_v2):
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PartyName')}/{cbc('Name')}"
    assert parsed_xml_v2.findtext(path) == "IYT Corporation"


def test_generate_xml_v2_party_name_omitted_when_absent(valid_data, minimal_buyer_data):
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", minimal_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PartyName')}"
    assert root.find(path) is None


def test_generate_xml_v2_buyer_id(parsed_xml_v2):
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PartyIdentification')}/{cbc('ID')}"
    assert parsed_xml_v2.findtext(path) == "buyer-001"


def test_generate_xml_v2_buyer_address_street_from_buyer_data(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('PostalAddress')}/{cbc('StreetName')}")
    assert parsed_xml_v2.findtext(path) == "56A Avon Way"


def test_generate_xml_v2_buyer_address_city_from_buyer_data(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('PostalAddress')}/{cbc('CityName')}")
    assert parsed_xml_v2.findtext(path) == "Bridgtow"


def test_generate_xml_v2_buyer_address_country_from_buyer_data(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('PostalAddress')}/{cac('Country')}/{cbc('IdentificationCode')}")
    assert parsed_xml_v2.findtext(path) == "GB"


def test_generate_xml_v2_buyer_address_omitted_when_absent(valid_data, minimal_buyer_data):
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", minimal_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PostalAddress')}"
    assert root.find(path) is None


def test_generate_xml_v2_tax_scheme_registration_name(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('PartyTaxScheme')}/{cbc('RegistrationName')}")
    assert parsed_xml_v2.findtext(path) == "Bridgtow District Council"


def test_generate_xml_v2_tax_scheme_company_id(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('PartyTaxScheme')}/{cbc('CompanyID')}")
    assert parsed_xml_v2.findtext(path) == "12356478"


def test_generate_xml_v2_tax_scheme_exemption_reason(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('PartyTaxScheme')}/{cbc('ExemptionReason')}")
    assert parsed_xml_v2.findtext(path) == "Local Authority"


def test_generate_xml_v2_tax_scheme_id(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('PartyTaxScheme')}/{cac('TaxScheme')}/{cbc('ID')}")
    assert parsed_xml_v2.findtext(path) == "UK VAT"


def test_generate_xml_v2_tax_scheme_type_code(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('PartyTaxScheme')}/{cac('TaxScheme')}/{cbc('TaxTypeCode')}")
    assert parsed_xml_v2.findtext(path) == "VAT"


def test_generate_xml_v2_tax_scheme_omitted_when_absent(valid_data, minimal_buyer_data):
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", minimal_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('PartyTaxScheme')}"
    assert root.find(path) is None


def test_generate_xml_v2_contact_name(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('Contact')}/{cbc('Name')}")
    assert parsed_xml_v2.findtext(path) == "Mr Fred Churchill"


def test_generate_xml_v2_contact_telephone(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('Contact')}/{cbc('Telephone')}")
    assert parsed_xml_v2.findtext(path) == "0127 2653214"


def test_generate_xml_v2_contact_telefax(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('Contact')}/{cbc('Telefax')}")
    assert parsed_xml_v2.findtext(path) == "0127 2653215"


def test_generate_xml_v2_contact_email(parsed_xml_v2):
    path = (f"{cac('BuyerCustomerParty')}/{cac('Party')}"
            f"/{cac('Contact')}/{cbc('ElectronicMail')}")
    assert parsed_xml_v2.findtext(path) == "fred@iytcorporation.gov.uk"


def test_generate_xml_v2_contact_omitted_when_absent(valid_data, minimal_buyer_data):
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", minimal_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('BuyerCustomerParty')}/{cac('Party')}/{cac('Contact')}"
    assert root.find(path) is None


def test_generate_xml_v2_delivery_address_street(parsed_xml_v2):
    path = f"{cac('Delivery')}/{cac('DeliveryAddress')}/{cbc('StreetName')}"
    assert parsed_xml_v2.findtext(path) == "123 Main St"


def test_generate_xml_v2_delivery_address_city(parsed_xml_v2):
    path = f"{cac('Delivery')}/{cac('DeliveryAddress')}/{cbc('CityName')}"
    assert parsed_xml_v2.findtext(path) == "Sydney"


def test_generate_xml_v2_delivery_address_country(parsed_xml_v2):
    path = (f"{cac('Delivery')}/{cac('DeliveryAddress')}"
            f"/{cac('Country')}/{cbc('IdentificationCode')}")
    assert parsed_xml_v2.findtext(path) == "AU"


def test_generate_xml_v2_delivery_address_omitted_when_no_address(valid_data, full_buyer_data):
    valid_data.pop("address")
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", full_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('Delivery')}/{cac('DeliveryAddress')}"
    assert root.find(path) is None


def test_generate_xml_v2_delivery_start_date(valid_data, full_buyer_data):
    valid_data["delivery_start_date"] = "2024-01-18"
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", full_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('Delivery')}/{cac('RequestedDeliveryPeriod')}/{cbc('StartDate')}"
    assert root.findtext(path) == "2024-01-18"


def test_generate_xml_v2_delivery_start_date_omitted_when_absent(parsed_xml_v2):
    path = f"{cac('Delivery')}/{cac('RequestedDeliveryPeriod')}/{cbc('StartDate')}"
    assert parsed_xml_v2.find(path) is None


def test_generate_xml_v2_delivery_start_time(valid_data, full_buyer_data):
    valid_data["delivery_start_time"] = "09:00:00"
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", full_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('Delivery')}/{cac('RequestedDeliveryPeriod')}/{cbc('StartTime')}"
    assert root.findtext(path) == "09:00:00"


def test_generate_xml_v2_delivery_end_time(valid_data, full_buyer_data):
    valid_data["delivery_end_time"] = "17:00:00"
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", full_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('Delivery')}/{cac('RequestedDeliveryPeriod')}/{cbc('EndTime')}"
    assert root.findtext(path) == "17:00:00"


def test_generate_xml_v2_delivery_end_date_always_present(parsed_xml_v2):
    path = f"{cac('Delivery')}/{cac('RequestedDeliveryPeriod')}/{cbc('EndDate')}"
    assert parsed_xml_v2.findtext(path) == "2024-01-20"


def test_generate_xml_v2_no_delivery_block_when_no_delivery_date(valid_data, full_buyer_data):
    valid_data.pop("delivery_date")
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", full_buyer_data)
    root = etree.fromstring(xml_bytes)
    assert root.find(cac("Delivery")) is None


def test_generate_xml_v2_single_item_as_dict(valid_data, full_buyer_data):
    valid_data["items"] = {"item_name": "Widget A", "unit_price": 10.00, "quantity": 2}
    xml_bytes = generate_xml_v2(valid_data, "order-001", "buyer-001", full_buyer_data)
    root = etree.fromstring(xml_bytes)
    path = f"{cac('OrderLine')}/{cac('LineItem')}/{cac('Item')}/{cbc('Name')}"
    assert root.findtext(path) == "Widget A"