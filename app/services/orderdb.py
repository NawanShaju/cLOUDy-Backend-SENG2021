from flask import jsonify

def create_order_db(db, data, buyerId):
    
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
    
    address_id = insert_address(db, data.get("address"))
    product_ids = insert_product(db, data.get("items"))
    order_id = insert_order(db, data, buyerId, address_id[0][0])
    insert_order_item(db, data.get("items"), order_id[0][0], product_ids)
    
    return order_id
    
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



def update_order_service(db, buyerId, orderId, data):
    result = update_order_db(db, data, buyerId, orderId)
    return result


def update_order_db(db, data, buyerId, orderId):
    
    if data.get("address"):
        address_id = insert_address(db, data.get("address"))
        data["address_id"] = address_id[0][0]

    if data.get("items"):
        product_ids = update_order_product(db, data.get("items"))
        update_order_items(db, orderId, data.get("items"), product_ids)

    order = update_order_input(db, data, buyerId, orderId)

    return order


def update_order_input(db, data, buyerId, orderId):
    query = """
        UPDATE orders SET
            order_date      = COALESCE(%(order_date)s, order_date),
            delivery_date   = COALESCE(%(delivery_date)s, delivery_date),
            currency_code   = COALESCE(%(currency_code)s, currency_code),
            address_id      = COALESCE(%(address_id)s, address_id),
            status          = COALESCE(%(status)s, status)
        WHERE order_id = %(orderId)s
        AND external_buyer_id = %(buyerId)s
        RETURNING *
    """

    params = {
        "order_date":    data.get("order_date"),
        "delivery_date": data.get("delivery_date"),
        "currency_code": data.get("currency_code"),
        "address_id":    data.get("address_id"),
        "status":        data.get("status"),
        "orderId":       orderId,
        "buyerId":       buyerId
    }

    return db.execute_insert_update_delete(query, params)


def update_order_items(db, order_id, items, product_map):
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
        DO UPDATE SET
            quantity    = EXCLUDED.quantity,
            total_price = EXCLUDED.total_price
    """

    for item in items:
        product_id = product_map[item["item_name"]]

        params = {
            "order_id":    order_id,
            "product_id":  product_id,
            "quantity":    int(item.get("quantity")),
            "total_price": item.get("unit_price") * item.get("quantity")
        }

        db.execute_insert_update_delete(query, params)

def update_order_product(db, items):
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
            product_name        = EXCLUDED.product_name,
            product_description = EXCLUDED.product_description,
            unit_price          = EXCLUDED.unit_price
        RETURNING product_id
    """

    product_map = {}

    for item in items:
        result = db.execute_insert_update_delete(query, item)
        product_map[item["item_name"]] = result[0]

    return product_map

def cancel_order_service(db, buyer_id, order_id):
    result = cancel_order_db(db, buyer_id, order_id)
    return result


def cancel_order_db(db, buyer_id, order_id):
    order = get_order_db(db, buyer_id, order_id)
    
    if not order:
        return {"status": 404, "error": "Order not found"}
    print("here")
    print(order)
    print(order[1])
    print(buyer_id)
    if order[1] != buyer_id:
        return {"status": 403, "error": "Forbidden - buyer does not have access to this order"}

    if order[6] in ("CANCELED", "PROCESSED", "FINALISED"):
        return {"status": 409, "error": "Order cannot be deleted due to current status"}

    cancel_order_input(db, order_id)

    return {
        "orderId": order_id,
        "status": "CANCELED",
        "message": "Order deleted successfully"
    }


def get_order_db(db, buyer_id, order_id):
    query = """
        SELECT * FROM orders
        WHERE order_id = %(order_id)s
        AND external_buyer_id = %(buyer_id)s
    """
    params = {
        "order_id": order_id,
        "buyer_id": buyer_id
    }
    result = db.execute_query(query, params)
    return result


def cancel_order_input(db, order_id):
    query = """
        UPDATE orders
        SET status = 'CANCELED'
        WHERE order_id = %(order_id)s
    """
    params = {"order_id": order_id}
    db.execute_insert_update_delete(query, params)