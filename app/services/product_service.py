from app.services.db_services.product_db import (
    insert_product_v2,
    update_product_v2,
    delete_product_v2,
    get_products_by_seller,
    get_product_by_id_db,
    product_has_order_items,
    link_product_inventory,
    unlink_product_inventory,
)
from app.services.db_services.seller_db import get_seller_by_id
from app.services.db_services.inventory_db import (
    get_inventory_item_by_id,
    get_inventory_items_for_product,
)
from database.PostgresDB import PostgresDB


def _validate_inventory_items(db, seller_id, inventory_items):
    if not isinstance(inventory_items, list) or len(inventory_items) == 0:
        return "inventory_items must be a non-empty array"

    seen = set()
    for item in inventory_items:
        inv_id = item.get("inventory_id")
        if not inv_id:
            return "Each inventory item must have an inventory_id"

        qty = item.get("quantity_required", 1)
        if not isinstance(qty, int) or qty < 1:
            return f"quantity_required must be a positive integer for inventory_id {inv_id}"

        if inv_id in seen:
            return f"Duplicate inventory_id {inv_id}"
        seen.add(inv_id)

        existing = get_inventory_item_by_id(db, inv_id, seller_id)
        if not existing:
            return f"Inventory item {inv_id} not found or does not belong to this seller"

    return None


def _format_inventory_items(rows):
    return [
        {
            "inventoryId":       str(r[0]),
            "quantityRequired":  r[1],
            "itemName":          r[2],
            "itemDescription":   r[3],
            "purchasePrice":     str(r[4]) if r[4] is not None else None,
            "quantityAvailable": r[5],
        }
        for r in (rows or [])
    ]


def create_product_service(db, seller_id, data):
    if not data.get("product_name"):
        return {"error": "product_name is required"}, 400
    if "unit_price" not in data:
        return {"error": "unit_price is required"}, 400
    if not isinstance(data["unit_price"], (int, float)) or data["unit_price"] < 0:
        return {"error": "unit_price must be a non-negative number"}, 400

    seller = get_seller_by_id(db, seller_id)
    if not seller:
        return {"error": "Seller not found"}, 404

    # Validate inventory items if provided
    inventory_items = data.get("inventory_items")
    if inventory_items is not None:
        error = _validate_inventory_items(db, seller_id, inventory_items)
        if error:
            return {"error": error}, 400

    result = insert_product_v2(db, data, seller_id)
    product_id = str(result[0][0])

    if inventory_items:
        link_product_inventory(db, product_id, inventory_items)

    return {"product_id": product_id}


def update_product_service(db, product_id, seller_id, data):
    if not data:
        return {"error": "Request body cannot be empty"}, 400
    if "unit_price" in data:
        if not isinstance(data["unit_price"], (int, float)) or data["unit_price"] < 0:
            return {"error": "unit_price must be a non-negative number"}, 400

    product = get_product_by_id_db(db, product_id)
    if not product:
        return {"error": "Product not found"}, 404
    if str(product[4]) != str(seller_id):
        return {"error": "Forbidden - product does not belong to this seller"}, 403

    # If inventory_items provided, replace all links
    if "inventory_items" in data:
        inventory_items = data["inventory_items"]
        if inventory_items is None or inventory_items == []:
            # Passing null/empty array = unlink all
            unlink_product_inventory(db, product_id)
        else:
            error = _validate_inventory_items(db, seller_id, inventory_items)
            if error:
                return {"error": error}, 400
            unlink_product_inventory(db, product_id)
            link_product_inventory(db, product_id, inventory_items)

    result = update_product_v2(db, product_id, seller_id, data)
    if result is None and "inventory_items" not in data:
        return {"error": "No valid fields provided for update"}, 400

    return {"product_id": str(product_id), "message": "Product updated successfully"}


def delete_product_service(db, product_id, seller_id):
    product = get_product_by_id_db(db, product_id)
    if not product:
        return {"error": "Product not found"}, 404
    if str(product[4]) != str(seller_id):
        return {"error": "Forbidden - product does not belong to this seller"}, 403

    if product_has_order_items(db, product_id):
        return {
            "error": "Product cannot be deleted because it is referenced by existing order items"
        }, 409

    # Junction rows cascade via FK, but being explicit is fine too
    delete_product_v2(db, product_id, seller_id)
    return {"product_id": str(product_id), "message": "Product deleted successfully"}


def get_products_for_seller_service(db, seller_id):
    seller = get_seller_by_id(db, seller_id)
    if not seller:
        return {"error": "Seller not found"}, 404

    rows = get_products_by_seller(db, seller_id)
    products = []
    for row in (rows or []):
        pid = str(row[0])
        inv_rows = get_inventory_items_for_product(db, pid)
        products.append({
            "productId":          pid,
            "productName":        row[1],
            "productDescription": row[2],
            "unitPrice":          str(row[3]),
            "createdAt":          row[4].isoformat() if row[4] else None,
            "updatedAt":          row[5].isoformat() if row[5] else None,
            "imageUrl":           row[6],
            "inventoryItems":     _format_inventory_items(inv_rows),
        })

    return products


def get_product_by_id_service(db, product_id):
    row = get_product_by_id_db(db, product_id)
    if not row:
        return None

    inv_rows = get_inventory_items_for_product(db, product_id)
    return {
        "productId":          str(row[0]),
        "productName":        row[1],
        "productDescription": row[2],
        "unitPrice":          str(row[3]),
        "sellerId":           str(row[4]) if row[4] else None,
        "sellerName":         row[7],
        "createdAt":          row[5].isoformat() if row[5] else None,
        "updatedAt":          row[6].isoformat() if row[6] else None,
        "inventoryItems":     _format_inventory_items(inv_rows),
    }


def get_seller_products_internal(seller_id):
    with PostgresDB() as db:
        return get_products_for_seller_service(db, seller_id)
    

def get_products_by_api_key_service(db, api_key):
    # 1. Get client
    client = db.execute_query(
        "SELECT client_id FROM clients WHERE api_key = %(api_key)s",
        {"api_key": api_key}
    )

    if not client:
        return {"error": "Invalid API key"}, 401

    client_id = client[0]

    # 2. Get seller_ids linked to this client
    sellers = db.execute_query(
        """
        SELECT DISTINCT seller_id
        FROM registered_user
        WHERE client_id = %(client_id)s
        """,
        {"client_id": str(client_id)}
    )

    seller_ids = [row for row in sellers]

    if not seller_ids:
        return []

    # 3. Get products for all sellers
    query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.product_description,
            p.unit_price,
            p.created_at,
            p.updated_at,
            p.seller_id,
            s.party_name
        FROM products p
        LEFT JOIN sellers s ON p.seller_id = s.seller_id
        WHERE p.seller_id = ANY(%(seller_ids)s::uuid[])
        ORDER BY p.created_at DESC
    """

    rows = db.execute_query(query, {"seller_ids": seller_ids}, fetch_all=True)

    products = []
    for row in rows or []:
        products.append({
            "productId": str(row[0]),
            "productName": row[1],
            "productDescription": row[2],
            "unitPrice": str(row[3]),
            "createdAt": row[4].isoformat() if row[4] else None,
            "updatedAt": row[5].isoformat() if row[5] else None,
            "seller": {
                "sellerId": str(row[6]),
                "partyName": row[7],
            }
        })

    return products