from app.services.db_services.product_db import (
    insert_product_v2,
    update_product_v2,
    delete_product_v2,
    get_products_by_seller,
    get_product_by_id_db,
    product_has_order_items,
)
from app.services.db_services.seller_db import get_seller_by_id
from database.PostgresDB import PostgresDB


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

    result = insert_product_v2(db, data, seller_id)
    return {"product_id": str(result[0][0])}


def update_product_service(db, product_id, seller_id, data):
    if not data:
        return {"error": "Request body cannot be empty"}, 400

    if "unit_price" in data:
        if not isinstance(data["unit_price"], (int, float)) or data["unit_price"] < 0:
            return {"error": "unit_price must be a non-negative number"}, 400

    # Verify the product exists and belongs to this seller
    product = get_product_by_id_db(db, product_id)
    if not product:
        return {"error": "Product not found"}, 404

    if str(product[4]) != str(seller_id):
        return {"error": "Forbidden - product does not belong to this seller"}, 403

    result = update_product_v2(db, product_id, seller_id, data)
    if not result:
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

    result = delete_product_v2(db, product_id, seller_id)
    if not result:
        return {"error": "Failed to delete product"}, 500

    return {"product_id": str(product_id), "message": "Product deleted successfully"}


def get_products_for_seller_service(db, seller_id):
    seller = get_seller_by_id(db, seller_id)
    if not seller:
        return {"error": "Seller not found"}, 404

    rows = get_products_by_seller(db, seller_id)
    return [
        {
            "productId":          str(row[0]),
            "productName":        row[1],
            "productDescription": row[2],
            "unitPrice":          str(row[3]),
            "createdAt":          row[4].isoformat() if row[4] else None,
            "updatedAt":          row[5].isoformat() if row[5] else None,
        }
        for row in (rows or [])
    ]


def get_product_by_id_service(db, product_id):
    row = get_product_by_id_db(db, product_id)
    if not row:
        return None

    return {
        "productId":          str(row[0]),
        "productName":        row[1],
        "productDescription": row[2],
        "unitPrice":          str(row[3]),
        "sellerId":           str(row[4]) if row[4] else None,
        "sellerName":         row[7],
        "createdAt":          row[5].isoformat() if row[5] else None,
        "updatedAt":          row[6].isoformat() if row[6] else None,
    }
    
def get_seller_products_internal(seller_id):
    with PostgresDB() as db:
        return get_products_for_seller_service(
            db,
            seller_id
        )