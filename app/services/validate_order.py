import xml.etree.ElementTree as ET
from datetime import datetime

def validate_order(data, buyerId):
    
    if not buyerId:
        return "buyerId is not defined, please provide a valid buyerId"
    
    address = data.get("address")
    
    if not address:
        return "No address provided"

    for field in ["street", "city", "state", "postal_code"]:
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
        if not item.get("item_name"):
            return f"item_name is required."
        if "quantity" not in item or not isinstance(item["quantity"], int) or item["quantity"] <= 0:
            return f"quantity must be a positive integer."
        if "unit_price" not in item or not isinstance(item["unit_price"], (int, float)) or item["unit_price"] < 0:
            return f"unit_price must be a non-negative integer."
        
def validate_order_xml(xml_document: str):
    errors = []

    try:
        root = ET.fromstring(xml_document)
    except ET.ParseError as e:
        return False, [f"XML parsing error: {str(e)}"]

    if root.tag != "Order":
        errors.append("Root element must be <Order>")

    required_fields = ["orderId", "IssueDate", "DeliveryDate", "CurrencyCode", 
                       "BuyerCustomerParty", "Order"]
    
    for field in required_fields:
        if root.find(field) is None:
            errors.append(f"Missing required field: {field}")

    for date_field in ["IssueDate", "DeliveryDate"]:
        element = root.find(date_field)
        if element is not None:
            try:
                datetime.fromisoformat(element.text)
            except ValueError:
                errors.append(f"{date_field} must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")

    buyer = root.find("BuyerCustomerParty")
    if buyer is not None:
        if buyer.find("ID") is None:
            errors.append("BuyerCustomerParty must contain <ID>")
        address = buyer.find("Address")
        if address is None:
            errors.append("BuyerCustomerParty must contain <Address>")
        else:
            for subfield in ["Street", "City", "State", "Postal_code", "Country_code"]:
                if address.find(subfield) is None:
                    errors.append(f"Address missing required field: {subfield}")

    seller = root.find("SellerSupplierParty")
    if seller is not None:
        if seller.find("Name") is None:
            errors.append("SellerSupplierParty must contain <Name>")

    orders = root.find("Order")
    if orders is not None:
        order_items = orders.findall("Order")
        if not order_items:
            errors.append("There must be at least one <Order> inside <Order>")
        for i, item in enumerate(order_items, start=1):
            for subfield in ["ItemName", "Quantity", "Price", "ItemDescription"]:
                if item.find(subfield) is None:
                    errors.append(f"Order {i} missing field: {subfield}")

    is_valid = len(errors) == 0
    return is_valid, errors
    