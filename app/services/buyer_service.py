from .db_services.buyer_db import (
    buyer_has_existing_orders,
    get_buyers_by_api_key,
    insert_tax_scheme,
    insert_buyer,
    find_buyer_by_account_id,
    insert_auth,
    get_buyer_by_id,
    update_buyer,
    validate_buyer_ownership,
    delete_buyer
)
from database.PostgresDB import PostgresDB
from .db_services.order_db import insert_address

def create_buyer_service(db, data, api_key):
    if not data.get("party_name"):
        return {"error": "party_name is required"}, 400

    if not data.get("customer_assigned_account_id"):
        return {"error": "customer_assigned_account_id is required"}, 400

    existing = find_buyer_by_account_id(db, data.get("customer_assigned_account_id"))
    if existing:
        return {"error": "A buyer with this customer_assigned_account_id already exists"}, 409

    address_id = None
    if data.get("address"):
        result = insert_address(db, data["address"])
        address_id = result[0][0]

    tax_scheme_id = None
    if data.get("tax_scheme"):
        result = insert_tax_scheme(db, data["tax_scheme"])
        tax_scheme_id = result[0][0]

    buyer = insert_buyer(db, data, address_id, tax_scheme_id)
    buyer_id = str(buyer[0][0])

    insert_auth(db, api_key, buyer_id)

    return {"buyer_id": buyer_id}

def update_buyer_service(db, buyer_id, data, api_key):
    buyer = get_buyer_by_id(db, buyer_id)
    if not buyer:
        return {"error": "Buyer not found"}, 404

    if not validate_buyer_ownership(db, api_key, buyer_id):
        return {"error": "You are not authorised to update this buyer"}, 403

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

    updated = update_buyer(db, buyer_id, data, address_id, tax_scheme_id)
    if not updated:
        return {"error": "No valid fields provided for update"}, 400

    return {
        "buyer_id": str(buyer_id),
        "message": "Buyer updated successfully"
    }, 200


def delete_buyer_service(db, buyer_id, api_key):
    buyer = get_buyer_by_id(db, buyer_id)
    if not buyer:
        return {"error": "Buyer not found"}, 404

    if not validate_buyer_ownership(db, api_key, buyer_id):
        return {"error": "You are not authorised to delete this buyer"}, 403

    if buyer_has_existing_orders(db, buyer_id):
        return {
            "error": "Buyer cannot be deleted because related orders still exist. All related orders must be hard deleted first."
        }, 409

    deleted = delete_buyer(db, buyer_id)
    if not deleted:
        return {"error": "Failed to delete buyer"}, 500

    return {
        "buyer_id": str(buyer_id),
        "message": "Buyer deleted successfully"
    }, 200
    
def get_buyers_internal(api_key):

    with PostgresDB() as db:
        buyers = get_buyers_by_api_key(
            db,
            api_key
        )

    if not buyers:
        return []

    return [
        {
            "buyerId": str(row[0]),
            "party_name": row[1],
            "customer_assigned_account_id": row[2],
            "contact_name": row[3],
            "contact_email": row[4]
        }
        for row in buyers
    ]