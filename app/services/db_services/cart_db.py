def get_or_create_cart(db, seller_id):
    query = """
        INSERT INTO carts (seller_id)
        VALUES (%(seller_id)s)
        ON CONFLICT (seller_id) DO UPDATE 
        SET updated_at = CURRENT_TIMESTAMP
        RETURNING cart_id
    """
    return db.execute_insert_update_delete(query, {"seller_id": str(seller_id)})


def get_cart_by_seller(db, seller_id):
    query = """
        SELECT
            c.cart_id,
            c.seller_id,
            c.currency_code,
            c.created_at,
            c.updated_at
        FROM carts c
        WHERE c.seller_id = %(seller_id)s
    """
    return db.execute_query(query, {"seller_id": str(seller_id)})


def get_cart_items(db, cart_id):
    query = """
        SELECT
            ci.cart_item_id,
            ci.product_id,
            p.product_name,
            p.product_description,
            ci.unit_price,
            ci.quantity,
            (ci.unit_price * ci.quantity) AS line_total,
            ci.seller_id,
            s.party_name AS seller_name,
            ci.created_at,
            ci.updated_at,
            p.image_url
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.product_id
        JOIN sellers s ON ci.seller_id = s.seller_id
        WHERE ci.cart_id = %(cart_id)s
        ORDER BY ci.created_at ASC
    """
    return db.execute_query(query, {"cart_id": str(cart_id)}, fetch_all=True)


def add_cart_item(db, cart_id, product_id, seller_id, quantity, unit_price):
    query = """
        INSERT INTO cart_items (
            cart_id, product_id, seller_id, quantity, unit_price
        )
        VALUES (
            %(cart_id)s, %(product_id)s, %(seller_id)s, %(quantity)s, %(unit_price)s
        )
        ON CONFLICT (cart_id, product_id)
        DO UPDATE SET
            quantity   = cart_items.quantity + EXCLUDED.quantity,
            updated_at = CURRENT_TIMESTAMP
        RETURNING cart_item_id
    """
    return db.execute_insert_update_delete(query, {
        "cart_id":    str(cart_id),
        "product_id": str(product_id),
        "seller_id":  str(seller_id),
        "quantity":   quantity,
        "unit_price": unit_price,
    })


def update_cart_item_quantity(db, cart_id, product_id, quantity):
    query = """
        UPDATE cart_items
        SET quantity = %(quantity)s, updated_at = CURRENT_TIMESTAMP
        WHERE cart_id = %(cart_id)s AND product_id = %(product_id)s
        RETURNING cart_item_id
    """
    return db.execute_insert_update_delete(query, {
        "cart_id":    str(cart_id),
        "product_id": str(product_id),
        "quantity":   quantity,
    })


def remove_cart_item(db, cart_id, product_id):
    query = """
        DELETE FROM cart_items
        WHERE cart_id = %(cart_id)s AND product_id = %(product_id)s
        RETURNING cart_item_id
    """
    return db.execute_insert_update_delete(query, {
        "cart_id":    str(cart_id),
        "product_id": str(product_id),
    })


def clear_cart(db, cart_id):
    query = "DELETE FROM cart_items WHERE cart_id = %(cart_id)s"
    db.execute_insert_update_delete(query, {"cart_id": str(cart_id)})


def delete_cart(db, seller_id):
    query = "DELETE FROM carts WHERE seller_id = %(seller_id)s"
    db.execute_insert_update_delete(query, {"seller_id": str(seller_id)})


def get_cart_item(db, cart_id, product_id):
    query = """
        SELECT cart_item_id, cart_id, product_id, seller_id, quantity, unit_price
        FROM cart_items
        WHERE cart_id = %(cart_id)s AND product_id = %(product_id)s
    """
    return db.execute_query(query, {
        "cart_id":    str(cart_id),
        "product_id": str(product_id),
    })