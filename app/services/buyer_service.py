from .db_services.buyer_db import (
    insert_buyer_tax_scheme,
    insert_buyer,
    find_buyer_by_account_id,
)

from .db_services.order_db import insert_address

def create_buyer_service(db, data):
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
        result = insert_buyer_tax_scheme(db, data["tax_scheme"])
        tax_scheme_id = result[0][0]

    buyer = insert_buyer(db, data, address_id, tax_scheme_id)
    return {"buyer_id": str(buyer[0][0])}