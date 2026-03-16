from lxml import etree
from datetime import datetime
from ..utils.xml_generation import NS_CAC, NS_ORDER, NS_CBC

def validate_order(data, buyerId):
    
    if not buyerId:
        return "buyerId is not defined, please provide a valid buyerId"
    
    address = data.get("address")
    
    if not address:
        return "No address provided"
    
    if not isinstance(address, dict):
        return "wrong type for address please provide a dict and look at the swagger"

    for field in ["street", "city", "state", "postal_code", "country_code"]:
        if field not in address:
            return f"the required field {field} is missing"
                
    for date_field in ["order_date", "delivery_date"]:
        date = data.get(date_field)
        
        if not date:
            return f"{date_field} is required"
        
    if not data.get("currency_code"):
        return f"currency_code is required."
        
    
    items = data.get("items")
    
    if not items:
        return "no order was provided"
    
    if isinstance(items, dict):
        items = [items]
    
    for item in items:

        if not isinstance(item, dict):
            return f"wrong type for order please provide a dict and look at the swagger"    
        
        if not item.get("item_name"):
            return f"item_name is required."
        if "quantity" not in item or not isinstance(item["quantity"], int) or item["quantity"] <= 0:
            return f"quantity must be a positive integer."
        if "unit_price" not in item or not isinstance(item["unit_price"], (int, float)) or item["unit_price"] < 0:
            return f"unit_price must be a non-negative integer."
 
def cbc(tag):
    return f"{{{NS_CBC}}}{tag}"
 
def cac(tag):
    return f"{{{NS_CAC}}}{tag}"
 
def validate_order_xml(xml_document: str):
    errors = []
 
    # Parse XML
    try:
        if isinstance(xml_document, str):
            xml_document = xml_document.encode("utf-8")
        root = etree.fromstring(xml_document)
    except etree.XMLSyntaxError as e:
        return False, [f"XML parsing error: {str(e)}"]
 
    # Root element
    expected_root = f"{{{NS_ORDER}}}Order"
    if root.tag != expected_root:
        errors.append(f"Root element must be <Order> with UBL namespace '{NS_ORDER}', got: {root.tag}")
 
    # Required header fields
    required_cbc_fields = ["UBLVersionID", "ID", "IssueDate", "DocumentCurrencyCode"]
    for field in required_cbc_fields:
        if root.find(cbc(field)) is None:
            errors.append(f"Missing required field: <cbc:{field}>")
 
    # Date format validation
    for date_field in ["IssueDate"]:
        element = root.find(cbc(date_field))
        if element is not None and element.text:
            try:
                datetime.fromisoformat(element.text)
            except ValueError:
                errors.append(f"<cbc:{date_field}> must be in ISO format (YYYY-MM-DD), got: '{element.text}'")
 
    # Delivery date
    delivery = root.find(cac("Delivery"))
    if delivery is not None:
        period = delivery.find(cac("RequestedDeliveryPeriod"))
        if period is not None:
            end_date = period.find(cbc("EndDate"))
            if end_date is not None and end_date.text:
                try:
                    datetime.fromisoformat(end_date.text)
                except ValueError:
                    errors.append(f"Delivery <cbc:EndDate> must be in ISO format (YYYY-MM-DD), got: '{end_date.text}'")
 
    # BuyerCustomerParty
    buyer = root.find(cac("BuyerCustomerParty"))
    if buyer is None:
        errors.append("Missing required element: <cac:BuyerCustomerParty>")
    else:
        party = buyer.find(cac("Party"))
        if party is None:
            errors.append("<cac:BuyerCustomerParty> must contain a <cac:Party>")
        else:
            party_id = party.find(cac("PartyIdentification"))
            if party_id is None or party_id.find(cbc("ID")) is None:
                errors.append("<cac:BuyerCustomerParty> must contain <cac:PartyIdentification><cbc:ID>")
 
            address = party.find(cac("PostalAddress"))
            if address is None:
                errors.append("<cac:BuyerCustomerParty> must contain <cac:PostalAddress>")
            else:
                required_address_fields = ["StreetName", "CityName", "PostalZone"]
                for field in required_address_fields:
                    if address.find(cbc(field)) is None:
                        errors.append(f"<cac:PostalAddress> missing required field: <cbc:{field}>")
 
                country = address.find(cac("Country"))
                if country is None or country.find(cbc("IdentificationCode")) is None:
                    errors.append("<cac:PostalAddress> must contain <cac:Country><cbc:IdentificationCode>")
 
    # SellerSupplierParty
    seller = root.find(cac("SellerSupplierParty"))
    if seller is None:
        errors.append("Missing required element: <cac:SellerSupplierParty>")
    else:
        party = seller.find(cac("Party"))
        if party is None:
            errors.append("<cac:SellerSupplierParty> must contain a <cac:Party>")
        else:
            party_name = party.find(cac("PartyName"))
            if party_name is None or party_name.find(cbc("Name")) is None:
                errors.append("<cac:SellerSupplierParty> must contain <cac:PartyName><cbc:Name>")
 
    # OrderLine items
    order_lines = root.findall(cac("OrderLine"))
    if not order_lines:
        errors.append("Order must contain at least one <cac:OrderLine>")
    else:
        for i, order_line in enumerate(order_lines, start=1):
            line_item = order_line.find(cac("LineItem"))
            if line_item is None:
                errors.append(f"<cac:OrderLine> {i} must contain a <cac:LineItem>")
                continue
 
            # Required LineItem fields
            if line_item.find(cbc("ID")) is None:
                errors.append(f"OrderLine {i}: <cac:LineItem> missing <cbc:ID>")
 
            qty = line_item.find(cbc("Quantity"))
            if qty is None:
                errors.append(f"OrderLine {i}: <cac:LineItem> missing <cbc:Quantity>")
            else:
                if qty.get("unitCode") is None:
                    errors.append(f"OrderLine {i}: <cbc:Quantity> missing 'unitCode' attribute")
                try:
                    if float(qty.text) <= 0:
                        errors.append(f"OrderLine {i}: <cbc:Quantity> must be greater than 0")
                except (TypeError, ValueError):
                    errors.append(f"OrderLine {i}: <cbc:Quantity> must be a valid number")
 
            line_ext = line_item.find(cbc("LineExtensionAmount"))
            if line_ext is None:
                errors.append(f"OrderLine {i}: <cac:LineItem> missing <cbc:LineExtensionAmount>")
            elif line_ext.get("currencyID") is None:
                errors.append(f"OrderLine {i}: <cbc:LineExtensionAmount> missing 'currencyID' attribute")
 
            # Price block
            price = line_item.find(cac("Price"))
            if price is None:
                errors.append(f"OrderLine {i}: <cac:LineItem> missing <cac:Price>")
            else:
                price_amt = price.find(cbc("PriceAmount"))
                if price_amt is None:
                    errors.append(f"OrderLine {i}: <cac:Price> missing <cbc:PriceAmount>")
                elif price_amt.get("currencyID") is None:
                    errors.append(f"OrderLine {i}: <cbc:PriceAmount> missing 'currencyID' attribute")
 
            # Item block
            item = line_item.find(cac("Item"))
            if item is None:
                errors.append(f"OrderLine {i}: <cac:LineItem> missing <cac:Item>")
            else:
                if item.find(cbc("Name")) is None:
                    errors.append(f"OrderLine {i}: <cac:Item> missing <cbc:Name>")
 
    is_valid = len(errors) == 0
    return is_valid, errors
    