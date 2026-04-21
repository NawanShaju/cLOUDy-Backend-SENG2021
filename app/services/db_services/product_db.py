def insert_product_v2(db, data, seller_id):
    query = """
        INSERT INTO products (
            product_name,
            product_description,
            unit_price,
            seller_id
        )
        VALUES (
            %(product_name)s,
            %(product_description)s,
            %(unit_price)s,
            %(seller_id)s
        )
        ON CONFLICT (seller_id, product_name, product_description, unit_price)
        DO UPDATE SET product_name = EXCLUDED.product_name
        RETURNING product_id
    """
    params = {
        "product_name":        data.get("product_name"),
        "product_description": data.get("product_description"),
        "unit_price":          data.get("unit_price"),
        "seller_id":           seller_id,
    }
    return db.execute_insert_update_delete(query, params)


def link_product_inventory(db, product_id, inventory_items):
    for item in inventory_items:
        query = """
            INSERT INTO product_inventory (product_id, inventory_id, quantity_required)
            VALUES (%(product_id)s, %(inventory_id)s, %(quantity_required)s)
            ON CONFLICT (product_id, inventory_id)
            DO UPDATE SET quantity_required = EXCLUDED.quantity_required
        """
        db.execute_insert_update_delete(query, {
            "product_id":        str(product_id),
            "inventory_id":      str(item["inventory_id"]),
            "quantity_required": item.get("quantity_required", 1),
        })


def unlink_product_inventory(db, product_id):
    query = "DELETE FROM product_inventory WHERE product_id = %(product_id)s"
    db.execute_insert_update_delete(query, {"product_id": str(product_id)})


def update_product_v2(db, product_id, seller_id, data):
    fields = []
    params = {"product_id": str(product_id), "seller_id": str(seller_id)}

    if "product_name" in data:
        fields.append("product_name = %(product_name)s")
        params["product_name"] = data["product_name"]
    if "product_description" in data:
        fields.append("product_description = %(product_description)s")
        params["product_description"] = data["product_description"]
    if "unit_price" in data:
        fields.append("unit_price = %(unit_price)s")
        params["unit_price"] = data["unit_price"]

    if not fields:
        return None

    fields.append("updated_at = CURRENT_TIMESTAMP")
    query = f"""
        UPDATE products
        SET {", ".join(fields)}
        WHERE product_id = %(product_id)s
          AND seller_id = %(seller_id)s
        RETURNING product_id
    """
    return db.execute_insert_update_delete(query, params)


def get_products_by_seller(db, seller_id):
    query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.product_description,
            p.unit_price,
            p.created_at,
            p.updated_at,
            p.image_url
        FROM products p
        WHERE p.seller_id = %(seller_id)s
        ORDER BY p.created_at DESC
    """
    return db.execute_query(query, {"seller_id": str(seller_id)}, fetch_all=True)


def get_product_by_id_db(db, product_id):
    query = """
        SELECT
            p.product_id,
            p.product_name,
            p.product_description,
            p.unit_price,
            p.seller_id,
            p.created_at,
            p.updated_at,
            s.party_name AS seller_name
        FROM products p
        LEFT JOIN sellers s ON p.seller_id = s.seller_id
        WHERE p.product_id = %(product_id)s
    """
    return db.execute_query(query, {"product_id": str(product_id)})


def delete_product_v2(db, product_id, seller_id):
    query = """
        DELETE FROM products
        WHERE product_id = %(product_id)s
          AND seller_id = %(seller_id)s
        RETURNING product_id
    """
    return db.execute_insert_update_delete(query, {
        "product_id": str(product_id),
        "seller_id":  str(seller_id),
    })


def product_has_order_items(db, product_id):
    query = """
        SELECT 1 FROM order_items
        WHERE product_id = %(product_id)s
        LIMIT 1
    """
    return db.execute_query(query, {"product_id": str(product_id)})