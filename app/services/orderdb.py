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
        ON CONFLICT (product_name, product_description, unit_price)
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


def update_order_db(db, data, buyerId, orderId):
    
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
    
    check_query = """
        SELECT address_id
        FROM addresses
        WHERE street = %(street)s
        AND city = %(city)s
        AND state = %(state)s
        AND postal_code = %(postal_code)s
        AND country_code = %(country_code)s
    """
    
    existing_address = db.execute_query(check_query, merged)

    if existing_address:
        address_id = existing_address
    else:
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
        address_id = db.execute_insert_update_delete(query, merged)
        
    return address_id


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


def update_order_items(db, order_id, item, product_id):
    query = """
        UPDATE order_items
        SET
            quantity = COALESCE(%(quantity)s, quantity),
            total_price = COALESCE(%(total_price)s, total_price)
        WHERE order_id = %(order_id)s
        AND product_id = %(product_id)s
        RETURNING order_item_id
    """

    if not item.get("unit_price") or not item.get("quantity"):
        total_price = None
    else:
        total_price = item.get("unit_price") * item.get("quantity")

    params = {
        "order_id":    order_id,
        "product_id":  product_id,
        "quantity":    int(item["quantity"]) if item.get("quantity") is not None else None,
        "total_price": total_price
    }

    result = db.execute_insert_update_delete(query, params)
    
    if not result:
        return jsonify({"error": "Not Updated, invalid product id or order id"})


def update_order_product(db, item):
    
    check_query = """
        SELECT product_id
        FROM products
        WHERE product_name = %(item_name)s
        AND unit_price = %(unit_price)s
        AND product_description = %(item_description)s
        AND product_id != %(product_id)s
    """    
    
    params = {
        "item_name": item.get("item_name"),
        "item_description": item.get("item_description"),
        "unit_price": item.get("unit_price"),
        "product_id": item.get("product_id")
    }
    
    product_id = db.execute_query(check_query, params)
    
    if not product_id:
        query = """
            UPDATE products
            SET
                product_name = COALESCE(%(item_name)s, product_name),
                product_description = COALESCE(%(item_description)s, product_description),
                unit_price = COALESCE(%(unit_price)s, unit_price),
                updated_at = CURRENT_TIMESTAMP
            WHERE product_id = %(product_id)s
            RETURNING product_id
        """

        product_id = db.execute_insert_update_delete(query, params)

        if not product_id:
            return jsonify({"error": "The product id provided is invalid"}), 400

    return product_id


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
        "message": "Order canceled successfully"
    }


def get_order_db(db, buyer_id, order_id):
    query = """
        SELECT * FROM orders
        WHERE order_id = %(order_id)s
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

def delete_order_service(db, buyer_id, order_id):
    result = delete_order_db(db, buyer_id, order_id)
    return result


def delete_order_db(db, buyer_id, order_id):
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


def delete_order_documents(db, order_id):
    query = """
        DELETE FROM order_documents
        WHERE order_id = %(order_id)s
    """
    params = {"order_id": order_id}
    db.execute_insert_update_delete(query, params)


def delete_order_items(db, order_id):
    query = """
        DELETE FROM order_items
        WHERE order_id = %(order_id)s
    """
    params = {"order_id": order_id}
    db.execute_insert_update_delete(query, params)


def delete_order_input(db, order_id):
    query = """
        DELETE FROM orders
        WHERE order_id = %(order_id)s
    """
    params = {"order_id": order_id}
    db.execute_insert_update_delete(query, params)