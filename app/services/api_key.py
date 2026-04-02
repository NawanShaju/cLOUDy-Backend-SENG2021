from database.PostgresDB import PostgresDB
from functools import wraps
from flask import request, jsonify
from app.services.db_services.buyer_db import validate_buyer_ownership
import secrets
import bcrypt


def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )

def get_api_key(db, username, password):
    
    if not username:
        raise ValueError("Please provide a valid username")
        
    if not password:
        raise ValueError("Please provide a valid password")

    username = username.lower()
    
    query = """
        SELECT api_key, password
        FROM clients
        WHERE username = %s
    """
    
    result = db.execute_query(query, (username,))
    
    if not result:
        api_key = "ubl_sk_" + secrets.token_hex(24)
        password = hash_password(password)
        
        insert_query = """
            INSERT INTO clients (
                username, 
                password, 
                api_key
            )
            VALUES (
                %(username)s,
                %(password)s,
                %(api_key)s
            );
        """
        
        insert_params = {
            "username": username,
            "password": password,
            "api_key": api_key
        }
        
        db.execute_insert_update_delete(insert_query, insert_params)
    else:
        api_key, hashed_password = result
        
        if not verify_password(password, hashed_password): 
            raise PermissionError("The password is incorrect")
        
    return api_key
    

def validate_api_key(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        api_key = request.headers.get("api-key")

        with PostgresDB() as db:
            key_is_valid = db.execute_query(
                "SELECT api_key FROM clients WHERE api_key = %s",
                (api_key,)
            )

            if not key_is_valid:
                return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return decorated

def validate_buyer_auth(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("api-key")
        buyer_id = kwargs.get("buyerId")

        with PostgresDB() as db:
            owned = validate_buyer_ownership(db, api_key, buyer_id)

        if not owned:
            return jsonify({"error": "You don't own this buyer"}), 403
        
        return f(*args, **kwargs)
    
    return decorated