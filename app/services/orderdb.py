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

def update_order_service(db, buyerId, orderId, data):
    result = update_order_db(db, data, buyerId, orderId)
    return result


def update_order_db(db, data, buyerId, orderId):
    
    if data.get("address"):
        address_id = update_address(db, data.get("address"), orderId)
        data["address_id"] = address_id[0][0]

    if data.get("items"):
        product_ids = update_order_product(db, data.get("items"))
        update_order_items(db, orderId, data.get("items"), product_ids)

    order = update_order_input(db, data, buyerId, orderId)

    return order


def update_address(db, address, orderId):

    get_query = """
        SELECT a.street, a.city, a.state, a.postal_code, a.country_code
        FROM addresses a
        JOIN orders o ON o.address_id = a.address_id
        WHERE o.order_id = %(order_id)s
    """
    existing = db.execute_query(get_query, {"order_id": orderId})

    merged = {
        "street":       address.get("street")       if address.get("street")       is not None else existing[0],
        "city":         address.get("city")         if address.get("city")         is not None else existing[1],
        "state":        address.get("state")        if address.get("state")        is not None else existing[2],
        "postal_code":  address.get("postal_code")  if address.get("postal_code")  is not None else existing[3],
        "country_code": address.get("country_code") if address.get("country_code") is not None else existing[4]
    }

    query = """
        INSERT INTO addresses (
            street, city, state, postal_code, country_code
        )
        VALUES (
            %(street)s, %(city)s, %(state)s, %(postal_code)s, %(country_code)s
        )
        ON CONFLICT (street, city, state, postal_code, country_code)
        DO UPDATE SET street = EXCLUDED.street
        RETURNING address_id
    """

    result = db.execute_insert_update_delete(query, merged)
    return result

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

def get_full_order_db(db, buyer_id, order_id):
    query = """
        SELECT 
            o.order_date,
            o.delivery_date,
            o.currency_code,
            o.status,
            a.street,
            a.city,
            a.state,
            a.postal_code,
            a.country_code,
            json_agg(json_build_object(
                'item_name', p.product_name,
                'item_description', p.product_description,
                'unit_price', p.unit_price,
                'quantity', oi.quantity
            )) AS items
        FROM orders o
        LEFT JOIN addresses a ON o.address_id = a.address_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE o.order_id = %(order_id)s
        AND o.external_buyer_id = %(buyer_id)s
        GROUP BY o.order_date, o.delivery_date, o.currency_code, 
                 o.status, a.street, a.city, a.state, a.postal_code, a.country_code
    """
    params = {"order_id": order_id, "buyer_id": buyer_id}
    result = db.execute_query(query, params)
    
    if not result:
        return None

    row = result
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

def get_orders_for_buyer_db(db, buyerId, status=None, from_date=None, to_date=None, limit=10, offset=0):
    buyer_check_query = """
        SELECT 1
        FROM orders
        WHERE external_buyer_id = %(buyer_id)s
        LIMIT 1
    """

    buyer_exists = db.execute_query(buyer_check_query, {"buyer_id": buyerId})

    if not buyer_exists:
        return None
    
    query = """
       SELECT
            o.order_id,
            o.status,
            o.order_date,
            o.delivery_date,
            o.currency_code,
            COUNT(oi.order_item_id) AS item_count,
            COALESCE(SUM(oi.total_price), 0) AS total_amount
        FROM orders o
        LEFT JOIN order_items oi
            ON o.order_id = oi.order_id
        WHERE o.external_buyer_id = %(buyer_id)s
    """

    params = {
        "buyer_id": buyerId,
        "limit": limit,
        "offset": offset
    }

    if status:
        query += " AND UPPER(o.status) = UPPER(%(status)s)"
        params["status"] = status.strip()

    if from_date:
        query += " AND o.order_date >= %(from_date)s::date"
        params["from_date"] = from_date

    if to_date:
        query += " AND o.order_date <= %(to_date)s::date"
        params["to_date"] = to_date

    query += """
        GROUP BY
            o.order_id,
            o.status,
            o.order_date,
            o.delivery_date,
            o.currency_code
        ORDER BY o.order_date DESC, o.order_id
        LIMIT %(limit)s
        OFFSET %(offset)s
    """
    results = db.execute_query(query, params, fetch_all=True)

    orders = []

    for row in results:
        orders.append({
            "orderId": str(row[0]),
            "status": row[1],
            "orderDate": row[2].isoformat() if row[2] else None,
            "deliveryDate": row[3].isoformat() if row[3] else None,
            "currencyCode": row[4],
            "itemCount": row[5],
            "totalAmount": str(row[6]) if row[6] is not None else "0"
        })

    return orders
