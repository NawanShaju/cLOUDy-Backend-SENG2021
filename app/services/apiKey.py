from functools import wraps
from flask import request, jsonify
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
        return jsonify({"error": "Please provide a valid username"}), 400
        
    if not password:
        return jsonify({"error": "Please provide a valid password"}), 400
    
    query = """
        SELECT api_key, password
        FROM clients
        WHERE username = %s
    """
    
    api_key, hashed_password = db.execute_query(query, (username,))

    if not verify_password(password, hashed_password): 
        return jsonify({"error": "the password is incorrect"}), 401
    
    if not api_key:
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
        
        # db.execute_insert_update_delete(insert_query, insert_params)
        
    return api_key
    

# def require_api_key(f):

#     @wraps(f)
#     def decorated(*args, **kwargs):

#         api_key = request.headers.get("x-api-key")

#         if not api_key or api_key not in VALID_API_KEYS:
#             return jsonify({
#                 "status": 401,
#                 "error": "Unauthorized"
#             }), 401

#         return f(*args, **kwargs)

#     return decorated