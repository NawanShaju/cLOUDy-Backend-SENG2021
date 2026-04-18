def get_registered_user_by_email(db, email):
    query = """
        SELECT user_id, email, username, api_key, seller_id
        FROM registered_user
        WHERE LOWER(email) = %(email)s
    """
    return db.execute_query(query, {"email": email.lower()})


def get_registered_user_by_username(db, username):
    query = """
        SELECT user_id, email, username, api_key, seller_id
        FROM registered_user
        WHERE username = %(username)s
    """
    return db.execute_query(query, {"username": username})


def get_registered_user_by_api_key(db, api_key):
    query = """
        SELECT user_id, email, username, api_key, seller_id
        FROM registered_user
        WHERE api_key = %(api_key)s
    """
    return db.execute_query(query, {"api_key": api_key})


def insert_registered_user(db, email, username, api_key, seller_id):
    query = """
        INSERT INTO registered_user (
            email,
            username,
            api_key,
            seller_id
        )
        VALUES (
            %(email)s,
            %(username)s,
            %(api_key)s,
            %(seller_id)s
        )
        RETURNING user_id, email, username, api_key, seller_id
    """
    return db.execute_insert_update_delete(query, {
        "email": email.lower(),
        "username": username,
        "api_key": api_key,
        "seller_id": str(seller_id)
    })