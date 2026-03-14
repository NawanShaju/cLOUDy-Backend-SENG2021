import pytest
from app.services.validate_order import validate_order_xml

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
  <cac:AnticipatedMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="AUD">75.00</cbc:LineExtensionAmount>
    <cbc:PayableAmount currencyID="AUD">75.00</cbc:PayableAmount>
  </cac:AnticipatedMonetaryTotal>
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">50</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">75.00</cbc:LineExtensionAmount>
      <cac:Price>
        <cbc:PriceAmount currencyID="AUD">1.50</cbc:PriceAmount>
      </cac:Price>
      <cac:Item>
        <cbc:Description>High-strength steel bolt</cbc:Description>
        <cbc:Name>Steel Bolt</cbc:Name>
      </cac:Item>
    </cac:LineItem>
  </cac:OrderLine>
</Order>"""


def make_xml(**overrides):
    """
    Build a minimal valid UBL Order XML string, substituting named sections.
    Supported keys: ubl_version, order_id, issue_date, currency, buyer_block,
                    seller_block, order_lines
    """
    defaults = dict(
        ubl_version="2.1",
        order_id="ca21f797-379a-4e27-a703-4992c5ea46fa",
        issue_date="2026-04-05",
        currency="AUD",
        buyer_block="""
  <cac:BuyerCustomerParty>
    <cac:Party>
      <cac:PartyIdentification><cbc:ID>buyer-001</cbc:ID></cac:PartyIdentification>
      <cac:PostalAddress>
        <cbc:StreetName>10 Pitt St</cbc:StreetName>
        <cbc:CityName>Sydney</cbc:CityName>
        <cbc:PostalZone>2000</cbc:PostalZone>
        <cac:Country><cbc:IdentificationCode>AU</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
    </cac:Party>
  </cac:BuyerCustomerParty>""",
        seller_block="""
  <cac:SellerSupplierParty>
    <cac:Party>
      <cac:PartyName><cbc:Name>Acme Supplies</cbc:Name></cac:PartyName>
    </cac:Party>
  </cac:SellerSupplierParty>""",
        order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">10</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""",
    )
    defaults.update(overrides)
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<Order xmlns="urn:oasis:names:specification:ubl:schema:xsd:Order-2"
       xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
       xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:UBLVersionID>{defaults['ubl_version']}</cbc:UBLVersionID>
  <cbc:ID>{defaults['order_id']}</cbc:ID>
  <cbc:IssueDate>{defaults['issue_date']}</cbc:IssueDate>
  <cbc:DocumentCurrencyCode>{defaults['currency']}</cbc:DocumentCurrencyCode>
  {defaults['buyer_block']}
  {defaults['seller_block']}
  {defaults['order_lines']}
</Order>"""

class TestValidDocument:
    def test_fully_valid_document_passes(self):
        is_valid, errors = validate_order_xml(VALID_XML)
        assert is_valid is True
        assert errors == []

    def test_accepts_bytes_input(self):
        is_valid, errors = validate_order_xml(VALID_XML)
        assert is_valid is True

    def test_accepts_string_input(self):
        is_valid, errors = validate_order_xml(VALID_XML.decode("utf-8"))
        assert is_valid is True

    def test_valid_document_with_delivery_date(self):
        xml = make_xml(order_lines="""
  <cac:Delivery>
    <cac:RequestedDeliveryPeriod>
      <cbc:EndDate>2026-05-01</cbc:EndDate>
    </cac:RequestedDeliveryPeriod>
  </cac:Delivery>
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">10</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is True

    def test_valid_document_with_multiple_order_lines(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">5</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">50.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Bolt</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>2</cbc:ID>
      <cbc:Quantity unitCode="EA">3</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">60.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">20.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Nut</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is True

class TestMalformedXML:
    def test_empty_string_fails(self):
        is_valid, errors = validate_order_xml("")
        assert is_valid is False
        assert any("parsing error" in e.lower() for e in errors)

    def test_unclosed_tag_fails(self):
        is_valid, errors = validate_order_xml("<Order><cbc:ID>123</Order>")
        assert is_valid is False
        assert any("parsing error" in e.lower() for e in errors)

    def test_random_string_fails(self):
        is_valid, errors = validate_order_xml("not xml at all")
        assert is_valid is False
        assert any("parsing error" in e.lower() for e in errors)

class TestRootElement:
    def test_wrong_root_tag_fails(self):
        xml = make_xml().replace(
            'xmlns="urn:oasis:names:specification:ubl:schema:xsd:Order-2"',
            'xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"',
        )
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("Root element" in e for e in errors)

    def test_missing_ubl_namespace_fails(self):
        xml = """<?xml version='1.0' encoding='UTF-8'?>
<Order>
  <ID>123</ID>
</Order>"""
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("Root element" in e for e in errors)

class TestRequiredHeaderFields:
    @pytest.mark.parametrize("field,placeholder", [
        ("UBLVersionID", "<cbc:UBLVersionID>2.1</cbc:UBLVersionID>"),
        ("ID", "<cbc:ID>ca21f797-379a-4e27-a703-4992c5ea46fa</cbc:ID>"),
        ("IssueDate", "<cbc:IssueDate>2026-04-05</cbc:IssueDate>"),
        ("DocumentCurrencyCode", "<cbc:DocumentCurrencyCode>AUD</cbc:DocumentCurrencyCode>"),
    ])
    def test_missing_header_field_fails(self, field, placeholder):
        xml = make_xml().replace(placeholder, "")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any(field in e for e in errors)

class TestDateValidation:
    def test_invalid_issue_date_format_fails(self):
        is_valid, errors = validate_order_xml(make_xml(issue_date="05-04-2026"))
        assert is_valid is False
        assert any("IssueDate" in e for e in errors)

    def test_issue_date_as_text_fails(self):
        is_valid, errors = validate_order_xml(make_xml(issue_date="not-a-date"))
        assert is_valid is False
        assert any("IssueDate" in e for e in errors)

    def test_valid_issue_date_passes(self):
        is_valid, errors = validate_order_xml(make_xml(issue_date="2026-01-31"))
        assert is_valid is True

    def test_invalid_delivery_end_date_fails(self):
        xml = make_xml(order_lines="""
  <cac:Delivery>
    <cac:RequestedDeliveryPeriod>
      <cbc:EndDate>31-12-2026</cbc:EndDate>
    </cac:RequestedDeliveryPeriod>
  </cac:Delivery>
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">1</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">10.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("EndDate" in e for e in errors)

class TestBuyerCustomerParty:
    def test_missing_buyer_party_fails(self):
        xml = make_xml(buyer_block="")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("BuyerCustomerParty" in e for e in errors)

    def test_buyer_missing_party_element_fails(self):
        xml = make_xml(buyer_block="<cac:BuyerCustomerParty></cac:BuyerCustomerParty>")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("cac:Party" in e for e in errors)

    def test_buyer_missing_party_id_fails(self):
        xml = make_xml(buyer_block="""
  <cac:BuyerCustomerParty>
    <cac:Party>
      <cac:PostalAddress>
        <cbc:StreetName>10 Pitt St</cbc:StreetName>
        <cbc:CityName>Sydney</cbc:CityName>
        <cbc:PostalZone>2000</cbc:PostalZone>
        <cac:Country><cbc:IdentificationCode>AU</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
    </cac:Party>
  </cac:BuyerCustomerParty>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("PartyIdentification" in e for e in errors)

    def test_buyer_missing_postal_address_fails(self):
        xml = make_xml(buyer_block="""
  <cac:BuyerCustomerParty>
    <cac:Party>
      <cac:PartyIdentification><cbc:ID>buyer-001</cbc:ID></cac:PartyIdentification>
    </cac:Party>
  </cac:BuyerCustomerParty>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("PostalAddress" in e for e in errors)

    @pytest.mark.parametrize("missing_field,tag", [
        ("StreetName",  "<cbc:StreetName>10 Pitt St</cbc:StreetName>"),
        ("CityName",    "<cbc:CityName>Sydney</cbc:CityName>"),
        ("PostalZone",  "<cbc:PostalZone>2000</cbc:PostalZone>"),
    ])
    def test_buyer_missing_address_subfield_fails(self, missing_field, tag):
        buyer = f"""
  <cac:BuyerCustomerParty>
    <cac:Party>
      <cac:PartyIdentification><cbc:ID>buyer-001</cbc:ID></cac:PartyIdentification>
      <cac:PostalAddress>
        <cbc:StreetName>10 Pitt St</cbc:StreetName>
        <cbc:CityName>Sydney</cbc:CityName>
        <cbc:PostalZone>2000</cbc:PostalZone>
        <cac:Country><cbc:IdentificationCode>AU</cbc:IdentificationCode></cac:Country>
      </cac:PostalAddress>
    </cac:Party>
  </cac:BuyerCustomerParty>""".replace(tag, "")
        is_valid, errors = validate_order_xml(make_xml(buyer_block=buyer))
        assert is_valid is False
        assert any(missing_field in e for e in errors)

    def test_buyer_missing_country_fails(self):
        xml = make_xml(buyer_block="""
  <cac:BuyerCustomerParty>
    <cac:Party>
      <cac:PartyIdentification><cbc:ID>buyer-001</cbc:ID></cac:PartyIdentification>
      <cac:PostalAddress>
        <cbc:StreetName>10 Pitt St</cbc:StreetName>
        <cbc:CityName>Sydney</cbc:CityName>
        <cbc:PostalZone>2000</cbc:PostalZone>
      </cac:PostalAddress>
    </cac:Party>
  </cac:BuyerCustomerParty>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("IdentificationCode" in e for e in errors)

class TestSellerSupplierParty:
    def test_missing_seller_party_fails(self):
        xml = make_xml(seller_block="")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("SellerSupplierParty" in e for e in errors)

    def test_seller_missing_party_element_fails(self):
        xml = make_xml(seller_block="<cac:SellerSupplierParty></cac:SellerSupplierParty>")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("cac:Party" in e for e in errors)

    def test_seller_missing_name_fails(self):
        xml = make_xml(seller_block="""
  <cac:SellerSupplierParty>
    <cac:Party>
      <cac:PartyName></cac:PartyName>
    </cac:Party>
  </cac:SellerSupplierParty>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("cbc:Name" in e for e in errors)

class TestOrderLines:
    def test_no_order_lines_fails(self):
        xml = make_xml(order_lines="")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("OrderLine" in e for e in errors)

    def test_order_line_missing_line_item_fails(self):
        xml = make_xml(order_lines="<cac:OrderLine></cac:OrderLine>")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("LineItem" in e for e in errors)

    def test_line_item_missing_id_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:Quantity unitCode="EA">10</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("cbc:ID" in e for e in errors)

    def test_line_item_missing_quantity_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("Quantity" in e for e in errors)

    def test_quantity_missing_unit_code_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity>10</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("unitCode" in e for e in errors)

    def test_quantity_zero_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">0</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">0.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">0.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("greater than 0" in e for e in errors)

    def test_quantity_non_numeric_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">ten</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("valid number" in e for e in errors)

    def test_line_extension_missing_currency_id_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">10</cbc:Quantity>
      <cbc:LineExtensionAmount>100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("LineExtensionAmount" in e and "currencyID" in e for e in errors)

    def test_missing_price_block_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">10</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("cac:Price" in e for e in errors)

    def test_price_amount_missing_currency_id_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">10</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount>10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Widget</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("PriceAmount" in e and "currencyID" in e for e in errors)

    def test_missing_item_block_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">10</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("cac:Item" in e for e in errors)

    def test_item_missing_name_fails(self):
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">10</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">100.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Description>A thing</cbc:Description></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("cbc:Name" in e for e in errors)

    def test_errors_reported_per_line(self):
        """Multiple broken lines should report errors for each individually."""
        xml = make_xml(order_lines="""
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:ID>1</cbc:ID>
      <cbc:Quantity unitCode="EA">5</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">50.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Good Item</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>
  <cac:OrderLine>
    <cac:LineItem>
      <cbc:Quantity unitCode="EA">3</cbc:Quantity>
      <cbc:LineExtensionAmount currencyID="AUD">30.00</cbc:LineExtensionAmount>
      <cac:Price><cbc:PriceAmount currencyID="AUD">10.00</cbc:PriceAmount></cac:Price>
      <cac:Item><cbc:Name>Bad Item — no ID</cbc:Name></cac:Item>
    </cac:LineItem>
  </cac:OrderLine>""")
        is_valid, errors = validate_order_xml(xml)
        assert is_valid is False
        assert any("OrderLine 2" in e for e in errors)
        assert not any("OrderLine 1" in e for e in errors)