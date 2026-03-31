from app.services.db_services.seller_db import (
    find_seller_by_account_id,
    insert_seller,
    get_seller_by_id,
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