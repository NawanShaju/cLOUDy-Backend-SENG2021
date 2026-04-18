import bcrypt

from app.services.db_services.registered_user_db import (
    get_registered_user_by_email,
    get_registered_user_by_username,
    get_registered_user_by_login,
    insert_registered_user,
)
from app.services.db_services.seller_db import get_seller_by_id
from app.services.seller_service import create_seller_service
from app.services.api_key import get_client_by_api_key


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password, hashed_password):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def register_app_user_service(db, data, api_key):
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password")
    seller_data = data.get("seller")

    if not email:
        return {"error": "email is required"}, 400

    if "@" not in email:
        return {"error": "email is invalid"}, 400

    if not username:
        return {"error": "username is required"}, 400

    if not password:
        return {"error": "password is required"}, 400

    if len(password) < 6:
        return {"error": "password must be at least 6 characters"}, 400

    if not seller_data:
        return {"error": "seller is required"}, 400

    if not (seller_data.get("party_name") or "").strip():
        return {"error": "seller party_name is required"}, 400

    client = get_client_by_api_key(db, api_key)
    if not client:
        return {"error": "Unauthorized"}, 401

    existing_email = get_registered_user_by_email(db, email)
    if existing_email:
        return {"error": "email already in use"}, 409

    existing_username = get_registered_user_by_username(db, username)
    if existing_username:
        return {"error": "username already in use"}, 409

    hashed_password = hash_password(password)

    seller_result = create_seller_service(db, seller_data)
    if isinstance(seller_result, tuple):
        return seller_result

    seller_id = seller_result["seller_id"]

    user_result = insert_registered_user(
        db=db,
        client_id=client[0],
        seller_id=seller_id,
        email=email,
        username=username,
        hashed_password=hashed_password
    )

    user_row = user_result[0]
    seller = get_seller_by_id(db, seller_id)

    return {
        "user": {
            "user_id": str(user_row[0]),
            "client_id": str(user_row[1]),
            "seller_id": str(user_row[2]),
            "email": user_row[3],
            "username": user_row[4],
        },
        "seller": seller
    }


def login_app_user_service(db, data, api_key):
    login = (data.get("login") or "").strip()
    password = data.get("password")

    if not login:
        return {"error": "login is required"}, 400

    if not password:
        return {"error": "password is required"}, 400

    client = get_client_by_api_key(db, api_key)
    if not client:
        return {"error": "Unauthorized"}, 401

    user = get_registered_user_by_login(db, login)
    if not user:
        return {"error": "Invalid credentials"}, 401

    if str(user[1]) != str(client[0]):
        return {"error": "Invalid credentials"}, 401

    if not verify_password(password, user[5]):
        return {"error": "Invalid credentials"}, 401

    seller = get_seller_by_id(db, user[2])

    return {
        "user": {
            "user_id": str(user[0]),
            "client_id": str(user[1]),
            "seller_id": str(user[2]),
            "email": user[3],
            "username": user[4],
        },
        "seller": seller
    }