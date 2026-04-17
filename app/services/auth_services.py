from app.services.api_key import get_api_key
from app.services.seller_service import create_seller_service
from app.services.db_services.seller_auth_db import (
    insert_seller_auth, get_seller_id_by_api_key,
)
from app.services.db_services.seller_db import get_seller_by_id

def register_auth_service(db, data):
    username = data.get("username")
    password = data.get("password")
    seller_data = data.get("seller")

    if not username:
        return {"error": "Add username Homie"}, 400
    
    if not password:
        return {"error": "Add password Homie"}, 400
    
    if not seller_data:
        return {"error": "Seller is required Homie"}, 400
    
    try:
        api_key = get_api_key(db, username, password)
    except ValueError as e:
        return {"error": str(e)}, 400
    except PermissionError as e:
        return {"error": str(e)}, 401
    except Exception as e:
        return {"error": str(e)}, 500
    
    existing_seller_row = get_seller_id_by_api_key(db, api_key)

    if existing_seller_row:
        seller_id = existing_seller_row[0] if isinstance(existing_seller_row, tuple) else existing_seller_row
        seller = get_seller_by_id(db, seller_id)
        return {
            "error": "A seller is already linked to this account homie",
            "seller": seller
        }, 409
    
    seller_result = create_seller_service(db, seller_data)

    if isinstance(seller_result, tuple):
        return seller_result
    
    seller_id = seller_result["seller_id"]
    insert_seller_auth(db, api_key, seller_id)
    seller = get_seller_by_id(db, seller_id)

    return {
        "apiKey": api_key,
        "seller": seller
    }

    
def login_auth_service(db, data):
    username = data.get("username")
    password = data.get("password")

    if not username:
        return {"error": "username is required homie"}, 400
    
    if not password:
        return {"error": "password is required homie"}, 400
    
    try:
        api_key = get_api_key(db, username, password)
    except ValueError as e:
        return {"error": str(e)}, 400
    except PermissionError as e:
        return {"error": str(e)}, 401
    except Exception as e:
        return {"error": str(e)}, 500
    
    seller_row = get_seller_id_by_api_key(db, api_key)
    seller = None

    if seller_row:
        seller_id = seller_row[0] if isinstance(seller_row, tuple) else seller_row
        seller = get_seller_by_id(db, seller_id)

    return {
        "apiKey": api_key,
        "seller": seller
    }