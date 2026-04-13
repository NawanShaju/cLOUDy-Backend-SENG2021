def get_order_details(db, buyerId, orderId):
    query = """
        SELECT
            o.order_id,
            o.status,
            oi.product_id,
            p.product_name,
            p.product_description,
            p.unit_price,
            oi.quantity,
            oi.total_price
        FROM orders o
        JOIN order_items oi
            ON o.order_id = oi.order_id
        LEFT JOIN products p
            ON oi.product_id = p.product_id
        WHERE o.order_id = %(order_id)s
            AND (
                o.external_buyer_id = %(buyer_id)s
                OR o.buyer_id::text = %(buyer_id)s
            )
    """
    params = {"order_id": orderId, "buyer_id": buyerId}
    return db.execute_query(query, params, fetch_all=True)

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

def insert_order_v2(db, data, buyerId, address_id):
    query = """
        INSERT INTO orders (
            buyer_id,
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
        "buyerId":       buyerId,
        "address_id":    address_id,
        "order_date":    data.get("order_date"),
        "delivery_date": data.get("delivery_date"),
        "currency_code": data.get("currency_code"),
        "status":        "CREATED"
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

def insert_product_v2(db, items, seller_id):
    query = """
        INSERT INTO products (
            product_name,
            product_description,
            unit_price,
            seller_id
        )
        VALUES (
            %(item_name)s,
            %(item_description)s,
            %(unit_price)s,
            %(seller_id)s
        )
        ON CONFLICT (product_name, product_description, unit_price, seller_id)
        DO UPDATE SET
            product_name = EXCLUDED.product_name
        RETURNING product_id
    """
    product_map = {}
    for item in items:
        item["seller_id"] = seller_id
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

def get_existing_address_by_order(db, orderId):
    query = """
        SELECT a.street, a.city, a.state, a.postal_code, a.country_code
        FROM addresses a
        JOIN orders o ON o.address_id = a.address_id
        WHERE o.order_id = %(order_id)s
    """
    return db.execute_query(query, {"order_id": orderId})


def find_address_by_fields(db, address_fields):
    query = """
        SELECT address_id
        FROM addresses
        WHERE street = %(street)s
        AND city = %(city)s
        AND state = %(state)s
        AND postal_code = %(postal_code)s
        AND country_code = %(country_code)s
    """
    return db.execute_query(query, address_fields)

def upsert_address(db, address_fields):
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
    return db.execute_insert_update_delete(query, address_fields)

def update_order(db, data, buyerId, orderId):
    query = """
        UPDATE orders SET
            order_date = COALESCE(%(order_date)s, order_date),
            delivery_date = COALESCE(%(delivery_date)s, delivery_date),
            currency_code = COALESCE(%(currency_code)s, currency_code),
            address_id = COALESCE(%(address_id)s, address_id),
            seller_id = COALESCE(%(seller_id)s, seller_id),
            status = COALESCE(%(status)s, status)
        WHERE order_id = %(orderId)s
            AND (
                external_buyer_id = %(buyer_id)s
                OR buyer_id::text = %(buyer_id)s
            )
        RETURNING *
    """
    params = {
        "order_date":    data.get("order_date"),
        "delivery_date": data.get("delivery_date"),
        "currency_code": data.get("currency_code"),
        "address_id":    data.get("address_id"),
        "seller_id":     data.get("seller_id"),
        "status":        data.get("status"),
        "orderId":       orderId,
        "buyer_id":      buyerId
    }
    return db.execute_insert_update_delete(query, params)

def update_order_items(db, order_id, item, product_id):
    query = """
        UPDATE order_items
        SET
            quantity = COALESCE(%(quantity)s, quantity),
            total_price = COALESCE(%(total_price)s, total_price),
            product_id = COALESCE(%(product_id)s, product_id)
        WHERE order_id = %(order_id)s
        RETURNING order_item_id
    """
    params = {
        "order_id":    order_id,
        "product_id":  product_id,
        "quantity":    int(item["quantity"]) if item.get("quantity") is not None else None,
        "total_price": item.get("unit_price") * item.get("quantity")
                       if item.get("unit_price") and item.get("quantity") else None
    }
    return db.execute_insert_update_delete(query, params)

def find_duplicate_product(db, item):
    query = """
        SELECT product_id
        FROM products
        WHERE product_name = %(item_name)s
        AND unit_price = %(unit_price)s
        AND product_description = %(item_description)s
        AND product_id != %(product_id)s
    """
    params = {
        "item_name":        item.get("item_name"),
        "item_description": item.get("item_description"),
        "unit_price":       item.get("unit_price"),
        "product_id":       item.get("product_id")
    }
    return db.execute_query(query, params)

def update_product(db, item):
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
    params = {
        "item_name":        item.get("item_name"),
        "item_description": item.get("item_description"),
        "unit_price":       item.get("unit_price"),
        "product_id":       item.get("product_id")
    }
    return db.execute_insert_update_delete(query, params)

def get_full_order(db, buyer_id, order_id):
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
            AND (
                o.external_buyer_id = %(buyer_id)s
                OR o.buyer_id::text = %(buyer_id)s
            )
        GROUP BY o.order_date, o.delivery_date, o.currency_code,
                 o.status, a.street, a.city, a.state, a.postal_code, a.country_code
    """
    params = {"order_id": order_id, "buyer_id": buyer_id}
    return db.execute_query(query, params)

def get_order_by_id(db, buyer_id, order_id):
    query = """
        SELECT * FROM orders
        WHERE order_id = %(order_id)s
    """
    params = {"order_id": order_id, "buyer_id": buyer_id}
    return db.execute_query(query, params, fetch_all=True)

def cancel_order(db, order_id):
    query = """
        UPDATE orders
        SET status = 'CANCELED'
        WHERE order_id = %(order_id)s
    """
    db.execute_insert_update_delete(query, {"order_id": order_id})

def get_orders_for_buyer(db, buyerId, status=None, from_date=None, to_date=None, limit=10, offset=0):
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
        WHERE (
            o.external_buyer_id = %(buyer_id)s
            OR o.buyer_id::text = %(buyer_id)s
        )
    """
    params = {"buyer_id": buyerId, "limit": limit, "offset": offset}

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
            o.order_id, o.status, o.order_date, o.delivery_date, o.currency_code
        ORDER BY o.order_date DESC, o.order_id
        LIMIT %(limit)s
        OFFSET %(offset)s
    """
    return db.execute_query(query, params, fetch_all=True)

def buyer_has_orders(db, buyer_id):
    query = """
        SELECT 1 FROM orders
        WHERE (
            external_buyer_id = %(buyer_id)s
            OR buyer_id::text = %(buyer_id)s
        )
        LIMIT 1
    """
    return db.execute_query(query, {"buyer_id": buyer_id})

def get_cancelled_orders_for_buyer(db, buyer_id):
    query = """
        SELECT order_id FROM orders
        WHERE (
            external_buyer_id = %(buyer_id)s
            OR buyer_id::text = %(buyer_id)s
        )
        AND status = 'CANCELED'
    """
    return db.execute_query(query, {"buyer_id": buyer_id}, fetch_all=True)

def delete_order_documents(db, order_id):
    query = """
        DELETE FROM order_documents
        WHERE order_id = %(order_id)s
    """
    db.execute_insert_update_delete(query, {"order_id": order_id})

def delete_order_items(db, order_id):
    query = """
        DELETE FROM order_items
        WHERE order_id = %(order_id)s
    """
    db.execute_insert_update_delete(query, {"order_id": order_id})

def delete_order(db, order_id):
    query = """
        DELETE FROM orders
        WHERE order_id = %(order_id)s
    """
    db.execute_insert_update_delete(query, {"order_id": order_id})
