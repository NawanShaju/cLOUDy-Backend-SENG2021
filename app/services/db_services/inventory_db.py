def insert_inventory_item(db, seller_id, data):
    query = """
        INSERT INTO inventory (seller_id, item_name, item_description, purchase_price, quantity)
        VALUES (%(seller_id)s, %(item_name)s, %(item_description)s, %(purchase_price)s, %(quantity)s)
        RETURNING inventory_id
    """
    return db.execute_insert_update_delete(query, {
        "seller_id":        str(seller_id),
        "item_name":        data.get("item_name"),
        "item_description": data.get("item_description"),
        "purchase_price":   data.get("purchase_price"),
        "quantity":         data.get("quantity"),
    })

def update_inventory_item(db, inventory_id, seller_id, data):
    fields = []
    params = {"inventory_id": str(inventory_id), "seller_id": str(seller_id)}

    if "item_name" in data:
        fields.append("item_name = %(item_name)s")
        params["item_name"] = data["item_name"]
    if "item_description" in data:
        fields.append("item_description = %(item_description)s")
        params["item_description"] = data["item_description"]
    if "purchase_price" in data:
        fields.append("purchase_price = %(purchase_price)s")
        params["purchase_price"] = data["purchase_price"]
    if "quantity" in data:
        fields.append("quantity = %(quantity)s")
        params["quantity"] = data["quantity"]

    if not fields:
        return None

    fields.append("updated_at = CURRENT_TIMESTAMP")
    query = f"""
        UPDATE inventory
        SET {", ".join(fields)}
        WHERE inventory_id = %(inventory_id)s
          AND seller_id = %(seller_id)s
        RETURNING inventory_id
    """
    return db.execute_insert_update_delete(query, params)

def delete_inventory_item(db, inventory_id, seller_id):
    query = """
        DELETE FROM inventory
        WHERE inventory_id = %(inventory_id)s
          AND seller_id = %(seller_id)s
        RETURNING inventory_id
    """
    return db.execute_insert_update_delete(query, {
        "inventory_id": str(inventory_id),
        "seller_id":    str(seller_id),
    })

def get_inventory_by_seller(db, seller_id):
    query = """
        SELECT inventory_id, item_name, item_description, purchase_price, quantity, created_at, updated_at
        FROM inventory
        WHERE seller_id = %(seller_id)s
        ORDER BY created_at DESC
    """
    return db.execute_query(query, {"seller_id": str(seller_id)}, fetch_all=True)

def get_inventory_item_by_id(db, inventory_id, seller_id):
    query = """
        SELECT inventory_id, item_name, item_description, purchase_price, quantity, created_at, updated_at
        FROM inventory
        WHERE inventory_id = %(inventory_id)s
          AND seller_id = %(seller_id)s
    """
    return db.execute_query(query, {
        "inventory_id": str(inventory_id),
        "seller_id":    str(seller_id),
    })