from flask import jsonify
from .orderdb import (
    insert_address, 
    insert_product, 
    insert_order, 
    insert_order_item,
    update_address,
    update_order_product,
    update_order_items,
    update_order_input,
    get_order_db,
    cancel_order_input,
    delete_order_documents,
    delete_order_items,
    delete_order_input
)

def create_order_service(db, data, buyerId):
    
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
    
    address_id = insert_address(db, data.get("address"))
    product_ids = insert_product(db, data.get("items"))
    order_id = insert_order(db, data, buyerId, address_id[0][0])
    insert_order_item(db, data.get("items"), order_id[0][0], product_ids)
    
    return order_id

def update_order_service(db, data, buyerId, orderId):
    
    if data.get("item") and data.get("item").get("product_id"):
        return jsonify({"error": "please provide a valid product_id"}), 400
    
    if data.get("address"):
        address_id = update_address(db, data.get("address"), orderId)
        data["address_id"] = address_id[0]

    if data.get("item"):
        product_id = update_order_product(db, data.get("item"))
        update_order_items(db, orderId, data.get("item"), product_id[0][0])

    order = update_order_input(db, data, buyerId, orderId)

    return order

def cancel_order_service(db, buyer_id, order_id):
    order = get_order_db(db, buyer_id, order_id)
    
    if not order:
        return {"status": 404, "error": "Order not found"}
    order = order[0]
    if order[1] != buyer_id:
        return {"status": 403, "error": "Forbidden - buyer does not have access to this order"}

    if order[6] in ("CANCELED", "PROCESSED", "FINALISED"):
        return {"status": 409, "error": "Order cannot be deleted due to current status"}

    cancel_order_input(db, order_id)

    return {
        "orderId": order_id,
        "status": "CANCELED",
        "message": "Order canceled successfully"
    }
    
    
def delete_order_service(db, buyer_id, order_id):
    order = get_order_db(db, buyer_id, order_id)

    if not order:
        return {"status": 404, "error": "Order not found"}

    if order[1] != buyer_id:
        return {"status": 403, "error": "Forbidden - buyer does not have access to this order"}

    if order[6] != "CANCELED":
        return {"status": 409, "error": "Order cannot be deleted unless status is CANCELED"}

    delete_order_documents(db, order_id)
    delete_order_items(db, order_id)
    delete_order_input(db, order_id)

    return {
        "orderId": order_id,
        "message": "Order deleted successfully"
    }
    
def delete_buyers_all_cancelled_orders_service(db, buyer_id):

    buyer_exists_query = """
        SELECT 1
        FROM orders
        WHERE external_buyer_id = %(buyer_id)s
    """
    buyer_exists = db.execute_query(buyer_exists_query, {"buyer_id": buyer_id})

    if not buyer_exists:
        return {"status": 404, "error": "Buyer not found"}

    cancelled_orders_query = """
        SELECT order_id
        FROM orders
        WHERE external_buyer_id = %(buyer_id)s
          AND status = 'CANCELED'
    """
    cancelled_orders = db.execute_query(cancelled_orders_query, 
                                        {"buyer_id": buyer_id}, 
                                        fetch_all=True)

    if not cancelled_orders:
        return {"status": 409, "error": "No canceled orders found for this buyer"}

    for row in cancelled_orders:
        order_id = row[0]
        delete_order_documents(db, order_id)
        delete_order_items(db, order_id)
        delete_order_input(db, order_id)

    return {"status": 200}
