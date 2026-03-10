from flask import jsonify
from database.PostgresDB import PostgresDB
from .xmldb import get_order_xml

def create_order_db(db, data, buyerId):
    
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
    
    address_id = insert_address(db, data.get("address"))
    product_ids = insert_product(db, data.get("items"))
    order_id = insert_order(db, data, buyerId, address_id[0][0])
    insert_order_item(db, data.get("items"), order_id[0][0], product_ids)
    
    return order_id
    
def get_order_details(db, buyerId, orderId):
    query = """
        SELECT
            o.order_id,
            oi.product_id,
            oi.quantity,
            oi.total_price,
            o.status
        FROM orders o
        JOIN order_items oi
            ON o.order_id = oi.order_id
        WHERE o.order_id = %(order_id)s
          AND o.external_buyer_id = %(buyer_id)s
    """

    params = {
        "order_id": orderId,
        "buyer_id": buyerId
    }
    
    result = db.execute_query(query, params)

    if not result:
        return None
    
    xml_content = get_order_xml(db, orderId)
    
    if not xml_content:
        return None

    return {
        "orderId": str(result[0]),
        "productId": str(result[1]) if result[1] is not None else None,
        "quantity": result[2],
        "money": result[3],
        "status": result[4],
        "xml": xml_content
    }

def insert_order_item(db, items, order_id, product_map):
    query = """
        INSERT INTO order_items (
            order_id,
            product_id,
            quantity,
            total_price
        )
        VALUES (
            %(order_id)s,
            %(product_id)s,
            %(quantity)s,
            %(total_price)s
        )
        ON CONFLICT (order_id, product_id)
        DO NOTHING
    """

    for item in items:
        product_id = product_map[item["item_name"]]

        params = {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": int(item.get("quantity")),
            "total_price": item.get("unit_price") * item.get("quantity")
        }

        db.execute_insert_update_delete(query, params)
    
    
def insert_order(db, data, buyerId, address_id):
    
    query = """
        INSERT INTO orders (
            external_buyer_id,
            address_id,
            order_date,
            delivery_date,
            currency_code,
            status
        ) 
        VALUES (
            %(buyerId)s,
            %(address_id)s,
            %(order_date)s,
            %(delivery_date)s,
            %(currency_code)s,
            %(status)s
        )
        RETURNING order_id
    """
    
    params = {
        "buyerId": buyerId,
        "address_id": address_id,
        "order_date": data.get("order_date"),
        "delivery_date": data.get("delivery_date"),
        "currency_code": data.get("currency_code"),
        "status": "CREATED"
    }
    
    return db.execute_insert_update_delete(query, params)

def insert_product(db, items):
    query = """
        INSERT INTO products (
            product_name,
            product_description,
            unit_price
        )
        VALUES (
            %(item_name)s,
            %(item_description)s,
            %(unit_price)s
        )
        ON CONFLICT (product_name, unit_price)
        DO UPDATE SET
            product_name = EXCLUDED.product_name
        RETURNING product_id
    """

    product_map = {}

    for item in items:
        result = db.execute_insert_update_delete(query, item)
        product_map[item["item_name"]] = result[0]

    return product_map
    

def insert_address(db, address):
    
    query = """
        INSERT INTO addresses (
            street,
            city,
            state,
            postal_code,
            country_code
        )
        VALUES (
            %(street)s,
            %(city)s,
            %(state)s,
            %(postal_code)s,
            %(country_code)s
        )
        ON CONFLICT (street, city, state, postal_code, country_code)
        DO UPDATE SET
            street = EXCLUDED.street
        RETURNING address_id
    """
        
    return db.execute_insert_update_delete(query, address)