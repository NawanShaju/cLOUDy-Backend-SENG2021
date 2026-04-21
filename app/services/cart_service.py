from app.services.db_services.cart_db import (
    get_or_create_cart,
    get_cart_by_seller,
    get_cart_items,
    get_cart_item,
    add_cart_item,
    update_cart_item_quantity,
    remove_cart_item,
    clear_cart,
    delete_cart,
)
from app.services.db_services.product_db import get_product_by_id_db
from app.services.db_services.seller_db import get_seller_by_id
from app.services.db_services.buyer_db import get_buyer_by_id
from app.services.db_services.order_db import (
    insert_address,
    insert_product,
    insert_order_v2,
    insert_order_item,
)
from app.services.db_services.buyer_db import insert_auth
from app.utils.xml_generation import generate_xml_v2
from app.services.db_services.xml_db import xml_to_db
from datetime import datetime, timezone
from app.services.db_services.inventory_db import get_inventory_items_for_product

def _format_cart(cart_row, items):
    seller_groups = {}
    grand_total   = 0

    for item in items:
        seller_id   = str(item[7])
        seller_name = item[8]
        line_total  = float(item[6])
        grand_total += line_total

        if seller_id not in seller_groups:
            seller_groups[seller_id] = {
                "sellerId":   seller_id,
                "sellerName": seller_name,
                "items":      [],
                "subtotal":   0,
            }

        seller_groups[seller_id]["items"].append({
            "cartItemId": str(item[0]),
            "productId": str(item[1]),
            "productName": item[2],
            "productDescription": item[3],
            "unitPrice": str(item[4]),
            "quantity": item[5],
            "lineTotal": str(round(line_total, 2)),
            "imageUrl": item[11],
            "addedAt": item[9].isoformat() if item[9] else None,
            "updatedAt": item[10].isoformat() if item[10] else None,
        })
        seller_groups[seller_id]["subtotal"] += line_total

    for s in seller_groups.values():
        s["subtotal"] = str(round(s["subtotal"], 2))

    return {
        "cartId": str(cart_row[0]),
        "sellerId": str(cart_row[1]),
        "currencyCode": cart_row[2],
        "grandTotal": str(round(grand_total, 2)),
        "itemCount": len(items),
        "sellers": list(seller_groups.values()),
    }


def get_cart_service(db, seller_id):
    cart = get_cart_by_seller(db, seller_id)
    if not cart:
        return {
            "sellerId":     seller_id,
            "cartId":       None,
            "grandTotal":   "0.00",
            "itemCount":    0,
            "sellers":      [],
        }

    items = get_cart_items(db, cart[0])
    return _format_cart(cart, items or [])

def add_to_cart_service(db, seller_id, data):
    if not data.get("product_id"):
        return {"error": "product_id is required"}, 400

    quantity = data.get("quantity", 1)
    if not isinstance(quantity, int) or quantity <= 0:
        return {"error": "quantity must be a positive integer"}, 400

    product = get_product_by_id_db(db, data["product_id"])
    if not product:
        return {"error": "Product not found"}, 404

    product_id        = str(product[0])
    product_seller_id = str(product[4])
    unit_price        = float(product[3])

    if not product_seller_id:
        return {"error": "Product is not associated with a seller"}, 400

    cart = get_or_create_cart(db, product_seller_id)
    cart_id = cart[0][0]

    existing_cart_item = get_cart_item(db, cart_id, product_id)
    existing_qty = existing_cart_item[4] if existing_cart_item else 0
    additional_qty = quantity  

    inv_items = get_inventory_items_for_product(db, product_id)
    if inv_items:
        insufficient = []
        for inv in inv_items:
            required  = inv[1] * additional_qty
            available = inv[5]
            if available < required:
                insufficient.append({
                    "itemName":  inv[2],
                    "required":  required,
                    "available": available,
                })
        if insufficient:
            return {
                "error": "Insufficient inventory for one or more required items",
                "items": insufficient,
            }, 409

        # Deduct inventory immediately
        for inv in inv_items:
            db.execute_insert_update_delete("""
                UPDATE inventory
                SET quantity = quantity - %(deduct)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE inventory_id = %(inventory_id)s
            """, {
                "inventory_id": str(inv[0]),
                "deduct": inv[1] * additional_qty,
            })

    add_cart_item(db, cart_id, product_id, product_seller_id, quantity, unit_price)

    items    = get_cart_items(db, cart_id)
    cart_row = get_cart_by_seller(db, product_seller_id)
    return _format_cart(cart_row, items or [])

def update_cart_item_service(db, seller_id, product_id, data):
    quantity = data.get("quantity")
    if quantity is None:
        return {"error": "quantity is required"}, 400
    if not isinstance(quantity, int) or quantity <= 0:
        return {"error": "quantity must be a positive integer"}, 400

    cart = get_cart_by_seller(db, seller_id)
    if not cart:
        return {"error": "Cart not found"}, 404

    cart_id = cart[0]
    existing = get_cart_item(db, cart_id, product_id)
    if not existing:
        return {"error": "Item not found in cart"}, 404

    old_qty = existing[4]
    delta   = quantity - old_qty

    inv_items = get_inventory_items_for_product(db, product_id)
    if inv_items and delta != 0:
        if delta > 0:
            insufficient = []
            for inv in inv_items:
                required  = inv[1] * delta
                available = inv[5]
                if available < required:
                    insufficient.append({
                        "itemName":  inv[2],
                        "required":  required,
                        "available": available,
                    })
            if insufficient:
                return {
                    "error": "Insufficient inventory",
                    "items": insufficient,
                }, 409

        for inv in inv_items:
            db.execute_insert_update_delete("""
                UPDATE inventory
                SET quantity = quantity - %(delta)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE inventory_id = %(inventory_id)s
            """, {
                "inventory_id": str(inv[0]),
                "delta": inv[1] * delta,
            })

    result = update_cart_item_quantity(db, cart_id, product_id, quantity)
    if not result:
        return {"error": "Item not found in cart"}, 404

    items    = get_cart_items(db, cart_id)
    cart_row = get_cart_by_seller(db, seller_id)
    return _format_cart(cart_row, items or [])

def remove_from_cart_service(db, seller_id, product_id):
    cart = get_cart_by_seller(db, seller_id)
    if not cart:
        return {"error": "Cart not found"}, 404

    cart_id  = cart[0]
    existing = get_cart_item(db, cart_id, product_id)
    if not existing:
        return {"error": "Item not found in cart"}, 404

    removed_qty = existing[4]

    # Restore inventory
    inv_items = get_inventory_items_for_product(db, product_id)
    for inv in (inv_items or []):
        db.execute_insert_update_delete("""
            UPDATE inventory
            SET quantity = quantity + %(restore)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE inventory_id = %(inventory_id)s
        """, {
            "inventory_id": str(inv[0]),
            "restore": inv[1] * removed_qty,
        })

    result = remove_cart_item(db, cart_id, product_id)
    if not result:
        return {"error": "Item not found in cart"}, 404

    items    = get_cart_items(db, cart_id)
    cart_row = get_cart_by_seller(db, seller_id)
    return _format_cart(cart_row, items or [])


def clear_cart_service(db, seller_id):
    cart = get_cart_by_seller(db, seller_id)
    if not cart:
        return {"error": "Cart not found"}, 404

    clear_cart(db, cart[0])
    delete_cart(db, seller_id)
    return {"message": "Cart cleared successfully"}


def checkout_service(db, seller_id, buyer_id, data, api_key):
    if not data.get("address"):
        return {"error": "address is required for checkout"}, 400

    for field in ["street", "city", "state", "postal_code", "country_code"]:
        if field not in data["address"]:
            return {"error": f"address.{field} is required"}, 400

    if not data.get("delivery_date"):
        return {"error": "delivery_date is required for checkout"}, 400
    if not data.get("currency_code"):
        return {"error": "currency_code is required for checkout"}, 400

    cart = get_cart_by_seller(db, seller_id)
    if not cart:
        return {"error": "Cart is empty"}, 400

    cart_id = cart[0]
    items   = get_cart_items(db, cart_id)
    if not items:
        return {"error": "Cart is empty"}, 400

    buyer_data = get_buyer_by_id(db, buyer_id)
    if not buyer_data:
        return {"error": "Buyer not found"}, 404

    price_changes = []
    for item in items:
        product = get_product_by_id_db(db, str(item[1]))
        current_px = float(product[3])
        cart_px = float(item[4])
        if current_px != cart_px:
            price_changes.append({
                "productId": str(item[1]),
                "productName": item[2],
                "cartPrice": str(cart_px),
                "currentPrice": str(current_px),
            })
    if price_changes:
        return {
            "error": "Some prices have changed since items were added to your cart",
            "priceChanges": price_changes,
            "message": "Please review and update your cart before checking out",
        }, 409

    seller_groups = {}
    for item in items:
        sid = str(item[7])
        if sid not in seller_groups:
            seller_groups[sid] = []
        seller_groups[sid].append(item)

    today = datetime.now(timezone.utc).date().isoformat()
    created_orders = []

    for order_seller_id, seller_items in seller_groups.items():
        seller_data = get_seller_by_id(db, order_seller_id)

        order_data = {
            "order_date":    today,
            "delivery_date": data["delivery_date"],
            "currency_code": data["currency_code"],
            "address":       data["address"],
            "seller_id":     order_seller_id,
            "items": [
                {
                    "item_name":        row[2],
                    "item_description": row[3],
                    "unit_price":       float(row[4]),
                    "quantity":         row[5],
                    "product_id":       str(row[1]),
                }
                for row in seller_items
            ],
        }

        address_id  = insert_address(db, order_data["address"])
        product_map = insert_product(db, order_data["items"], seller_id)
        order_id = insert_order_v2(db, order_data, buyer_id, address_id[0][0])
        insert_order_item(db, order_data["items"], order_id[0][0], product_map)
        insert_auth(db, api_key, buyer_id)

        xml_string = generate_xml_v2(
            order_data, order_id[0][0], buyer_id, buyer_data, seller_data
        )
        xml_to_db(db, xml_string, order_id[0][0])
        created_orders.append({
            "orderId":   str(order_id[0][0]),
            "sellerId":  order_seller_id,
            "itemCount": len(seller_items),
        })

    clear_cart(db, cart_id)
    delete_cart(db, seller_id)

    return {"message": "Checkout successful", "orders": created_orders}