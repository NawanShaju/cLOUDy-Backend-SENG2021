from app.services.db_services.inventory_db import (
    insert_inventory_item,
    update_inventory_item,
    delete_inventory_item,
    get_inventory_by_seller,
    get_inventory_item_by_id,
)

def create_inventory_service(db, seller_id, data):
    if not data.get("item_name"):
        return {"error": "item_name is required"}, 400
    if data.get("purchase_price") is None:
        return {"error": "purchase_price is required"}, 400
    if data.get("quantity") is None:
        return {"error": "quantity is required"}, 400
    if not isinstance(data["quantity"], int) or data["quantity"] < 0:
        return {"error": "quantity must be a non-negative integer"}, 400

    result = insert_inventory_item(db, seller_id, data)
    if not result:
        return {"error": "Failed to create inventory item"}, 500
    return {"inventoryId": str(result[0][0]), "message": "Inventory item created successfully"}

def update_inventory_service(db, seller_id, inventory_id, data):
    existing = get_inventory_item_by_id(db, inventory_id, seller_id)
    if not existing:
        return {"error": "Inventory item not found"}, 404

    result = update_inventory_item(db, inventory_id, seller_id, data)
    if result is None:
        return {"error": "No fields to update"}, 400
    return {"inventoryId": str(inventory_id), "message": "Inventory item updated successfully"}

def delete_inventory_service(db, seller_id, inventory_id):
    existing = get_inventory_item_by_id(db, inventory_id, seller_id)
    if not existing:
        return {"error": "Inventory item not found"}, 404

    delete_inventory_item(db, inventory_id, seller_id)
    return {"inventoryId": str(inventory_id), "message": "Inventory item deleted successfully"}

def get_inventory_service(db, seller_id):
    rows = get_inventory_by_seller(db, seller_id)

    if not rows:
        return {
            "sellerId": seller_id,
            "count": 0,
            "items": []
        }

    items = []
    for r in rows:
        items.append({
            "inventoryId": str(r[0]),
            "itemName": r[1],
            "itemDescription": r[2],
            "purchasePrice": str(r[3]) if r[3] is not None else None,
            "quantity": r[4],
            "createdAt": r[5].isoformat() if r[5] else None,
            "updatedAt": r[6].isoformat() if r[6] else None,
            "imageUrl": r[7],
        })

    return {
        "sellerId": seller_id,
        "count": len(items),
        "items": items
    }