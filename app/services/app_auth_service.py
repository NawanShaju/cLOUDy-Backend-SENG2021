from app.services.api_key import get_api_key
from app.services.seller_service import create_seller_service
from app.services.db_services.seller_db import get_seller_by_id
from app.services.db_services.registered_user_db import (
    get_registered_user_by_email,
    get_registered_user_by_username,
    get_registered_user_by_api_key,
    insert_registered_user,
)


def register_app_user_service(db, data):
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password")
    seller_data = data.get("seller")

    if not email:
        return {"error": "email is required"}, 400

    if not username:
        return {"error": "username is required"}, 400

    if not password:
        return {"error": "password is required"}, 400

    if not seller_data:
        return {"error": "seller is required"}, 400

    existing_email = get_registered_user_by_email(db, email)
    if existing_email:
        return {"error": "email already in use"}, 409

    existing_username = get_registered_user_by_username(db, username)
    if existing_username:
        return {"error": "username already in use"}, 409

    try:
        api_key = get_api_key(db, username, password)
    except ValueError as e:
        return {"error": str(e)}, 400
    except PermissionError as e:
        return {"error": str(e)}, 401
    except Exception as e:
        return {"error": str(e)}, 500

    existing_api_key_user = get_registered_user_by_api_key(db, api_key)
    if existing_api_key_user:
        return {"error": "This account is already registered"}, 409

    seller_result = create_seller_service(db, seller_data)
    if isinstance(seller_result, tuple):
        return seller_result

    seller_id = seller_result["seller_id"]

    user_result = insert_registered_user(
        db,
        email,
        username,
        api_key,
        seller_id
    )

    user_row = user_result[0]
    seller = get_seller_by_id(db, seller_id)

    return {
        "apiKey": api_key,
        "user": {
            "user_id": str(user_row[0]),
            "email": user_row[1],
            "username": user_row[2],
            "api_key": user_row[3],
            "seller_id": str(user_row[4]),
        },
        "seller": seller
    }


def login_app_user_service(db, data):
    username = (data.get("username") or "").strip()
    password = data.get("password")

    if not username:
        return {"error": "username is required"}, 400

    if not password:
        return {"error": "password is required"}, 400

    try:
        api_key = get_api_key(db, username, password)
    except ValueError as e:
        return {"error": str(e)}, 400
    except PermissionError as e:
        return {"error": str(e)}, 401
    except Exception as e:
        return {"error": str(e)}, 500

    user = get_registered_user_by_api_key(db, api_key)
    if not user:
        return {"error": "No registered app user found for this account"}, 404

    seller_id = user[4]
    seller = get_seller_by_id(db, seller_id)

    return {
        "apiKey": api_key,
        "user": {
            "user_id": str(user[0]),
            "email": user[1],
            "username": user[2],
            "api_key": user[3],
            "seller_id": str(user[4]),
        },
        "seller": seller
    }