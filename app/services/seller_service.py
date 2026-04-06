from app.services.db_services.seller_db import (
    find_seller_by_account_id,
    insert_seller,
    get_seller_by_id,
    update_seller,
    seller_has_existing_orders,
    delete_seller
)
from app.services.db_services.order_db import insert_address
from app.services.db_services.buyer_db import insert_tax_scheme


def create_seller_service(db, data):
    if not data.get("party_name"):
        return {"error": "party_name is required"}, 400

    if not data.get("customer_assigned_account_id"):
        return {"error": "customer_assigned_account_id is required"}, 400

    existing = find_seller_by_account_id(db, data.get("customer_assigned_account_id"))
    if existing:
        return {"error": "A seller with this customer_assigned_account_id already exists"}, 409

    address_id = None
    if data.get("address"):
        result = insert_address(db, data["address"])
        address_id = result[0][0]

    tax_scheme_id = None
    if data.get("tax_scheme"):
        result = insert_tax_scheme(db, data["tax_scheme"])
        tax_scheme_id = result[0][0]

    seller = insert_seller(db, data, address_id, tax_scheme_id)
    return {"seller_id": str(seller[0][0])}

def update_seller_service(db, seller_id, data):
    seller = get_seller_by_id(db, seller_id)
    if not seller:
        return {"error": "Seller not found"}, 404

    if not data:
        return {"error": "Request body cannot be empty"}, 400

    address_id = None
    if data.get("address"):
        result = insert_address(db, data["address"])
        address_id = result[0][0]

    tax_scheme_id = None
    if data.get("tax_scheme"):
        result = insert_tax_scheme(db, data["tax_scheme"])
        tax_scheme_id = result[0][0]

    updated = update_seller(db, seller_id, data, address_id, tax_scheme_id)
    if not updated:
        return {"error": "No valid fields provided for update"}, 400

    return {
        "seller_id": str(seller_id),
        "message": "Seller updated successfully"
    }


def delete_seller_service(db, seller_id):
    seller = get_seller_by_id(db, seller_id)
    if not seller:
        return {"error": "Seller not found"}, 404

    if seller_has_existing_orders(db, seller_id):
        return {
            "error": "Seller cannot be deleted because related orders still exist. All related orders must be hard deleted first."
        }, 409

    deleted = delete_seller(db, seller_id)
    if not deleted:
        return {"error": "Failed to delete seller"}, 500

    return {
        "seller_id": str(seller_id),
        "message": "Seller deleted successfully"
    }