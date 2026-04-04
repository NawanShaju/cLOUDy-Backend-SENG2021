from lxml import etree
from datetime import datetime, timezone
import uuid
 
# UBL 2.1 namespace declarations
NS_ORDER = "urn:oasis:names:specification:ubl:schema:xsd:Order-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
 
NSMAP = {
    None: NS_ORDER,
    "cac": NS_CAC,
    "cbc": NS_CBC,
}
 
def cbc(tag):
    return f"{{{NS_CBC}}}{tag}"
 
def cac(tag):
    return f"{{{NS_CAC}}}{tag}"

def _build_address_element(parent_el, address_data):
    if address_data.get("street"):
        etree.SubElement(parent_el, cbc("StreetName")).text = address_data["street"]
    if address_data.get("building_name"):
        etree.SubElement(parent_el, cbc("BuildingName")).text = address_data["building_name"]
    if address_data.get("building_number"):
        etree.SubElement(parent_el, cbc("BuildingNumber")).text = address_data["building_number"]
    if address_data.get("city"):
        etree.SubElement(parent_el, cbc("CityName")).text = address_data["city"]
    if address_data.get("postal_code"):
        etree.SubElement(parent_el, cbc("PostalZone")).text = address_data["postal_code"]
    if address_data.get("state"):
        etree.SubElement(parent_el, cbc("CountrySubentity")).text = address_data["state"]
    if address_data.get("address_line"):
        addr_line = etree.SubElement(parent_el, cac("AddressLine"))
        etree.SubElement(addr_line, cbc("Line")).text = address_data["address_line"]
    if address_data.get("country_code"):
        country = etree.SubElement(parent_el, cac("Country"))
        etree.SubElement(country, cbc("IdentificationCode")).text = address_data["country_code"]
        
def _build_tax_scheme(parent, tax):
    """Append a PartyTaxScheme block onto parent."""
    party_tax = etree.SubElement(parent, cac("PartyTaxScheme"))
    if tax.get("registration_name"):
        etree.SubElement(party_tax, cbc("RegistrationName")).text = tax["registration_name"]
    if tax.get("company_id"):
        etree.SubElement(party_tax, cbc("CompanyID")).text        = tax["company_id"]
    if tax.get("exemption_reason"):
        etree.SubElement(party_tax, cbc("ExemptionReason")).text  = tax["exemption_reason"]
    tax_scheme_el = etree.SubElement(party_tax, cac("TaxScheme"))
    if tax.get("scheme_id"):
        etree.SubElement(tax_scheme_el, cbc("ID")).text           = tax["scheme_id"]
    if tax.get("tax_type_code"):
        etree.SubElement(tax_scheme_el, cbc("TaxTypeCode")).text  = tax["tax_type_code"]
 
 
def _build_contact(parent, contact):
    """Append a Contact block onto parent."""
    contact_el = etree.SubElement(parent, cac("Contact"))
    if contact.get("name"):
        etree.SubElement(contact_el, cbc("Name")).text          = contact["name"]
    if contact.get("telephone"):
        etree.SubElement(contact_el, cbc("Telephone")).text     = contact["telephone"]
    if contact.get("telefax"):
        etree.SubElement(contact_el, cbc("Telefax")).text       = contact["telefax"]
    if contact.get("email"):
        etree.SubElement(contact_el, cbc("ElectronicMail")).text = contact["email"]

def generate_xml(data, orderId, buyerId):
    root = etree.Element("Order", nsmap=NSMAP)
 
    etree.SubElement(root, cbc("UBLVersionID")).text = "2.1"
    etree.SubElement(root, cbc("ID")).text = orderId
    etree.SubElement(root, cbc("UUID")).text = str(uuid.uuid4())
    etree.SubElement(root, cbc("IssueDate")).text = data.get(
        "order_date", datetime.now(timezone.utc).date().isoformat()
    )
    etree.SubElement(root, cbc("DocumentCurrencyCode")).text = data.get(
        "currency_code", "AUD"
    )
 
    buyer_party = etree.SubElement(root, cac("BuyerCustomerParty"))
    buyer_party_inner = etree.SubElement(buyer_party, cac("Party"))
 
    buyer_party_id = etree.SubElement(buyer_party_inner, cac("PartyIdentification"))
    etree.SubElement(buyer_party_id, cbc("ID")).text = buyerId
 
    address_data = data.get("address", {})
    if address_data:
        postal = etree.SubElement(buyer_party_inner, cac("PostalAddress"))
        _build_address_element(postal, address_data)
 
    seller_party = etree.SubElement(root, cac("SellerSupplierParty"))
    seller_party_inner = etree.SubElement(seller_party, cac("Party"))
    seller_name_el = etree.SubElement(seller_party_inner, cac("PartyName"))
    etree.SubElement(seller_name_el, cbc("Name")).text = data.get("supplier", "")
 
    delivery_date_str = data.get("delivery_date", "")
    if delivery_date_str:
        delivery = etree.SubElement(root, cac("Delivery"))
        
        if address_data:
            delivery_address = etree.SubElement(delivery, cac("DeliveryAddress"))
            _build_address_element(delivery_address, address_data)

        requested = etree.SubElement(delivery, cac("RequestedDeliveryPeriod"))
        if data.get("delivery_start_date"):
            etree.SubElement(requested, cbc("StartDate")).text = data["delivery_start_date"]
        if data.get("delivery_start_time"):
            etree.SubElement(requested, cbc("StartTime")).text = data["delivery_start_time"]
        etree.SubElement(requested, cbc("EndDate")).text = delivery_date_str
        if data.get("delivery_end_time"):
            etree.SubElement(requested, cbc("EndTime")).text = data["delivery_end_time"]
 
    currency_code = data.get("currency_code", "AUD")
    items_data = data.get("items", [])
    if isinstance(items_data, dict):
        items_data = [items_data]
 
    total = sum(
        float(item.get("unit_price", 0)) * int(item.get("quantity", 0))
        for item in items_data
    )
 
    monetary = etree.SubElement(root, cac("AnticipatedMonetaryTotal"))
    line_ext = etree.SubElement(monetary, cbc("LineExtensionAmount"))
    line_ext.set("currencyID", currency_code)
    line_ext.text = f"{total:.2f}"
    payable = etree.SubElement(monetary, cbc("PayableAmount"))
    payable.set("currencyID", currency_code)
    payable.text = f"{total:.2f}"
 
    for idx, item in enumerate(items_data, start=1):
        order_line = etree.SubElement(root, cac("OrderLine"))
        line_item = etree.SubElement(order_line, cac("LineItem"))
 
        etree.SubElement(line_item, cbc("ID")).text = str(idx)
 
        qty = etree.SubElement(line_item, cbc("Quantity"))
        qty.set("unitCode", item.get("unit_code", "EA"))
        qty.text = str(item.get("quantity", 0))
 
        unit_price = float(item.get("unit_price", 0))
        quantity = int(item.get("quantity", 0))
        line_total = unit_price * quantity
 
        line_ext_amt = etree.SubElement(line_item, cbc("LineExtensionAmount"))
        line_ext_amt.set("currencyID", currency_code)
        line_ext_amt.text = f"{line_total:.2f}"
 
        price_el = etree.SubElement(line_item, cac("Price"))
        price_amt = etree.SubElement(price_el, cbc("PriceAmount"))
        price_amt.set("currencyID", currency_code)
        price_amt.text = f"{unit_price:.2f}"
 
        item_el = etree.SubElement(line_item, cac("Item"))
        if item.get("item_description"):
            etree.SubElement(item_el, cbc("Description")).text = item["item_description"]
        etree.SubElement(item_el, cbc("Name")).text = item.get("item_name", "")
 
        if item.get("product_id"):
            sellers_id = etree.SubElement(item_el, cac("SellersItemIdentification"))
            etree.SubElement(sellers_id, cbc("ID")).text = item["product_id"]
 
    xml_bytes = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )
    
    return xml_bytes

def generate_xml_v2(data, orderId, buyerId, buyer_data, seller_data=None):
    root = etree.Element("Order", nsmap=NSMAP)

    etree.SubElement(root, cbc("UBLVersionID")).text = "2.1"
    etree.SubElement(root, cbc("ID")).text = orderId
    etree.SubElement(root, cbc("UUID")).text = str(uuid.uuid4())
    etree.SubElement(root, cbc("IssueDate")).text = data.get(
        "order_date", datetime.now(timezone.utc).date().isoformat()
    )
    etree.SubElement(root, cbc("DocumentCurrencyCode")).text = data.get("currency_code", "AUD")

    buyer_party = etree.SubElement(root, cac("BuyerCustomerParty"))

    if buyer_data.get("customer_assigned_account_id"):
        etree.SubElement(buyer_party, cbc("CustomerAssignedAccountID")).text = \
            buyer_data["customer_assigned_account_id"]
    if buyer_data.get("supplier_assigned_account_id"):
        etree.SubElement(buyer_party, cbc("SupplierAssignedAccountID")).text = \
            buyer_data["supplier_assigned_account_id"]

    buyer_party_inner = etree.SubElement(buyer_party, cac("Party"))

    if buyer_data.get("party_name"):
        party_name_el = etree.SubElement(buyer_party_inner, cac("PartyName"))
        etree.SubElement(party_name_el, cbc("Name")).text = buyer_data["party_name"]

    buyer_party_id = etree.SubElement(buyer_party_inner, cac("PartyIdentification"))
    etree.SubElement(buyer_party_id, cbc("ID")).text = buyerId

    if buyer_data.get("address"):
        postal = etree.SubElement(buyer_party_inner, cac("PostalAddress"))
        _build_address_element(postal, buyer_data["address"])

    if buyer_data.get("tax_scheme"):
        _build_tax_scheme(buyer_party_inner, buyer_data["tax_scheme"])

    if buyer_data.get("contact"):
        _build_contact(buyer_party_inner, buyer_data["contact"])

    seller_party       = etree.SubElement(root, cac("SellerSupplierParty"))
 
    if seller_data:
        if seller_data.get("customer_assigned_account_id"):
            etree.SubElement(seller_party, cbc("CustomerAssignedAccountID")).text = \
                seller_data["customer_assigned_account_id"]
        if seller_data.get("supplier_assigned_account_id"):
            etree.SubElement(seller_party, cbc("SupplierAssignedAccountID")).text = \
                seller_data["supplier_assigned_account_id"]
 
        seller_party_inner = etree.SubElement(seller_party, cac("Party"))
 
        if seller_data.get("party_name"):
            seller_name_el = etree.SubElement(seller_party_inner, cac("PartyName"))
            etree.SubElement(seller_name_el, cbc("Name")).text = seller_data["party_name"]
 
        seller_party_id = etree.SubElement(seller_party_inner, cac("PartyIdentification"))
        etree.SubElement(seller_party_id, cbc("ID")).text = seller_data["seller_id"]
 
        if seller_data.get("address"):
            postal = etree.SubElement(seller_party_inner, cac("PostalAddress"))
            _build_address_element(postal, seller_data["address"])
 
        if seller_data.get("tax_scheme"):
            _build_tax_scheme(seller_party_inner, seller_data["tax_scheme"])
 
        if seller_data.get("contact"):
            _build_contact(seller_party_inner, seller_data["contact"])
    else:
        seller_party_inner = etree.SubElement(seller_party, cac("Party"))
        seller_name_el = etree.SubElement(seller_party_inner, cac("PartyName"))
        etree.SubElement(seller_name_el, cbc("Name")).text = "No Seller Provided"
 
    address_data      = data.get("address", {})
    delivery_date_str = data.get("delivery_date", "")
    if delivery_date_str:
        delivery = etree.SubElement(root, cac("Delivery"))

        if address_data:
            delivery_address = etree.SubElement(delivery, cac("DeliveryAddress"))
            _build_address_element(delivery_address, address_data)

        requested = etree.SubElement(delivery, cac("RequestedDeliveryPeriod"))
        if data.get("order_date"):
            etree.SubElement(requested, cbc("StartDate")).text = data["order_date"]
            
        etree.SubElement(requested, cbc("EndDate")).text = delivery_date_str

    currency_code = data.get("currency_code", "AUD")
    items_data = data.get("items", [])
    if isinstance(items_data, dict):
        items_data = [items_data]

    total = sum(
        float(item.get("unit_price", 0)) * int(item.get("quantity", 0))
        for item in items_data
    )

    monetary = etree.SubElement(root, cac("AnticipatedMonetaryTotal"))
    line_ext = etree.SubElement(monetary, cbc("LineExtensionAmount"))
    line_ext.set("currencyID", currency_code)
    line_ext.text = f"{total:.2f}"
    payable = etree.SubElement(monetary, cbc("PayableAmount"))
    payable.set("currencyID", currency_code)
    payable.text = f"{total:.2f}"

    for idx, item in enumerate(items_data, start=1):
        order_line = etree.SubElement(root, cac("OrderLine"))
        line_item = etree.SubElement(order_line, cac("LineItem"))

        etree.SubElement(line_item, cbc("ID")).text = str(idx)

        qty = etree.SubElement(line_item, cbc("Quantity"))
        qty.set("unitCode", item.get("unit_code", "EA"))
        qty.text = str(item.get("quantity", 0))

        unit_price = float(item.get("unit_price", 0))
        quantity = int(item.get("quantity", 0))
        line_total = unit_price * quantity

        line_ext_amt = etree.SubElement(line_item, cbc("LineExtensionAmount"))
        line_ext_amt.set("currencyID", currency_code)
        line_ext_amt.text = f"{line_total:.2f}"

        price_el = etree.SubElement(line_item, cac("Price"))
        price_amt = etree.SubElement(price_el, cbc("PriceAmount"))
        price_amt.set("currencyID", currency_code)
        price_amt.text = f"{unit_price:.2f}"

        item_el = etree.SubElement(line_item, cac("Item"))
        if item.get("item_description"):
            etree.SubElement(item_el, cbc("Description")).text = item["item_description"]
        etree.SubElement(item_el, cbc("Name")).text = item.get("item_name", "")

        if item.get("product_id"):
            sellers_id = etree.SubElement(item_el, cac("SellersItemIdentification"))
            etree.SubElement(sellers_id, cbc("ID")).text = item["product_id"]
 
    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
