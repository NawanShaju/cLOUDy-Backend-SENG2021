from flask import jsonify
from .db_services.xml_db import get_order_xml
from .db_services.order_db import (
    get_full_order,
    get_order_details,
    insert_address,
    insert_product,
    insert_order,
    insert_order_item,
    get_existing_address_by_order,
    find_address_by_fields,
    upsert_address,
    update_order,
    update_order_items,
    find_duplicate_product,
    update_product,
    get_order_by_id,
    cancel_order,
    buyer_has_orders,
    get_cancelled_orders_for_buyer,
    get_orders_for_buyer,
    delete_order_documents,
    delete_order_items,
    delete_order,
)
from app.utils.helper import is_valid_uuid

def get_full_order_service(db, buyer_id, order_id):
    row = get_full_order(db, buyer_id, order_id)

    if not row:
        return None

    return {
        "order_date":    row[0].isoformat(),
        "delivery_date": row[1].isoformat(),
        "currency_code": row[2],
        "status":        row[3],
        "address": {
            "street":       row[4],
            "city":         row[5],
            "state":        row[6],
            "postal_code":  row[7],
            "country_code": row[8]
        },
        "items": row[9]
    }

def get_order_details_service(db, buyerId, orderId):
    results = get_order_details(db, buyerId, orderId)

    if not results:
        return None

    xml_content = get_order_xml(db, orderId)
    if not xml_content:
        return None

    return {
        "orderId": str(results[0][0]),
        "status": results[0][1],
        "items": [
            {
                "productId":          str(row[2]) if row[2] is not None else None,
                "productName":        row[3],
                "productDescription": row[4],
                "unitPrice":          str(row[5]) if row[5] is not None else None,
                "quantity":           row[6],
                "totalPrice":         str(row[7]) if row[7] is not None else None
            }
            for row in results
        ],
        "xml": xml_content
    }

def get_orders_for_buyer_service(db, buyerId, status=None, from_date=None, to_date=None, limit=10, offset=0):
    if not buyer_has_orders(db, buyerId):
        return None

    rows = get_orders_for_buyer(db, buyerId, status, from_date, to_date, limit, offset)

    return [
        {
            "orderId":      str(row[0]),
            "status":       row[1],
            "orderDate":    row[2].isoformat() if row[2] else None,
            "deliveryDate": row[3].isoformat() if row[3] else None,
            "currencyCode": row[4],
            "itemCount":    row[5],
            "totalAmount":  str(row[6]) if row[6] is not None else "0"
        }
        for row in rows
    ]

def create_order_service(db, data, buyerId):
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400

    address_id = insert_address(db, data.get("address"))
    product_map = insert_product(db, data.get("items"))
    order_id = insert_order(db, data, buyerId, address_id[0][0])
    insert_order_item(db, data.get("items"), order_id[0][0], product_map)

    return order_id

def _resolve_updated_address(db, incoming_address, orderId):
    existing = get_existing_address_by_order(db, orderId)

    merged = {
        "street":       incoming_address.get("street")       if incoming_address.get("street")       is not None else existing[0],
        "city":         incoming_address.get("city")         if incoming_address.get("city")         is not None else existing[1],
        "state":        incoming_address.get("state")        if incoming_address.get("state")        is not None else existing[2],
        "postal_code":  incoming_address.get("postal_code")  if incoming_address.get("postal_code")  is not None else existing[3],
        "country_code": incoming_address.get("country_code") if incoming_address.get("country_code") is not None else existing[4],
    }

    existing_address = find_address_by_fields(db, merged)
    if existing_address:
        return existing_address
    return upsert_address(db, merged)

def _resolve_updated_product(db, item):
    duplicate = find_duplicate_product(db, item)
    if duplicate:
        return duplicate

    product_id = update_product(db, item)
    if not product_id:
        raise ValueError("The product id provided is invalid")

    return product_id

def update_order_service(db, data, buyerId, orderId):
    if data.get("item") and not data.get("item").get("product_id"):
        return jsonify({"error": "please provide a valid product_id"}), 400
    
    if data.get("item") and not is_valid_uuid(data.get("item").get("product_id")):
        return jsonify({"error": "product_id most be a uuid"}), 400

    if data.get("address"):
        address_id = _resolve_updated_address(db, data.get("address"), orderId)
        data["address_id"] = address_id[0]

    if data.get("item"):
        try:
            product_id = _resolve_updated_product(db, data.get("item"))
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        result = update_order_items(db, orderId, data.get("item"), product_id[0][0])
        if not result:
            return jsonify({"error": "Not Updated, invalid product id or order id"}), 400

    order = update_order(db, data, buyerId, orderId)
    return order

def cancel_order_service(db, buyer_id, order_id):
    result = get_order_by_id(db, buyer_id, order_id)

    if not result:
        return {"status": 404, "error": "Order not found"}
    
    if result[1] != buyer_id:
        return {"status": 403, "error": "Forbidden - buyer does not have access to this order"}
    if result[6] in ("CANCELED", "PROCESSED", "FINALISED"):
        return {"status": 409, "error": "Order cannot be canceled due to current status"}

    cancel_order(db, order_id)
    return {
        "orderId": order_id,
        "status":  "CANCELED",
        "message": "Order canceled successfully"
    }

def delete_order_service(db, buyer_id, order_id):
    result = get_order_by_id(db, buyer_id, order_id)

    if not result:
        return {"status": 404, "error": "Order not found"}

    if result[1] != buyer_id:
        return {"status": 403, "error": "Forbidden - buyer does not have access to this order"}

    if result[6] != "CANCELED":
        return {"status": 409, "error": "Order cannot be deleted unless status is CANCELED"}

    delete_order_documents(db, order_id)
    delete_order_items(db, order_id)
    delete_order(db, order_id)

    return {"orderId": order_id, "message": "Order deleted successfully"}

def delete_buyers_all_cancelled_orders_service(db, buyer_id):
    if not buyer_has_orders(db, buyer_id):
        return {"status": 404, "error": "Buyer not found"}

    cancelled_orders = get_cancelled_orders_for_buyer(db, buyer_id)
    if not cancelled_orders:
        return {"status": 409, "error": "No canceled orders found for this buyer"}

    for row in cancelled_orders:
        order_id = row[0]
        delete_order_documents(db, order_id)
        delete_order_items(db, order_id)
        delete_order(db, order_id)

    return {"status": 200}
