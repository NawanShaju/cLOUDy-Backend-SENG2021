from lxml import etree
from datetime import datetime, timezone

def generate_xml(order_json):
    root = etree.Element("Order")

    # Order ID
    order_id = etree.SubElement(root, "ID")
    order_id.text = order_json.get("external_buyer_id", "ORD-0001")

    # IssueDate
    issue_date = etree.SubElement(root, "IssueDate")
    issue_date.text = order_json.get("order_date", datetime.now(timezone.utc).date().isoformat())

    # DeliveryDate
    delivery_date = etree.SubElement(root, "DeliveryDate")
    delivery_date.text = order_json.get("delivery_date", datetime.now(timezone.utc).date().isoformat())

    # Currency
    currency = etree.SubElement(root, "CurrencyCode")
    currency.text = order_json.get("currency_code", "USD")

    # Buyer info
    buyer = etree.SubElement(root, "BuyerCustomerParty")
    buyer_id = etree.SubElement(buyer, "ID")
    buyer_id.text = order_json.get("external_buyer_id", "UNKNOWN")

    # Address
    address_data = order_json.get("address", {})
    if address_data:
        address_el = etree.SubElement(buyer, "Address")
        for field in ["street", "city", "state", "postal_code", "country_code"]:
            field_el = etree.SubElement(address_el, field.capitalize())
            field_el.text = address_data.get(field, "")

    # Seller
    seller = etree.SubElement(root, "SellerSupplierParty")
    seller_name = etree.SubElement(seller, "Name")
    seller_name.text = order_json.get("supplier")

    # Order
    order = etree.SubElement(root, "Order")
    items_data = order_json.get("items", [])
    
    if isinstance(items_data, dict):
        items_data = [items_data]

    for item in items_data:
        line = etree.SubElement(order, "Order")
        item_name = etree.SubElement(line, "ItemName")
        item_name.text = item.get("item_name", "")

        quantity = etree.SubElement(line, "Quantity")
        quantity.text = str(item.get("quantity", 0))

        price = etree.SubElement(line, "Price")
        price.text = str(item.get("unit_price", 0))

        # Optional description
        if "item_description" in item:
            desc = etree.SubElement(line, "ItemDescription")
            desc.text = item.get("item_description", "")

    # Generate XML string
    xml_bytes = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8"
    )

    return xml_bytes