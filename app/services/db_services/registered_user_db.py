def get_registered_user_by_email(db, email):
    query = """
        SELECT user_id, client_id, seller_id, email, username, hashed_password
        FROM registered_user
        WHERE LOWER(email) = %(email)s
    """
    return db.execute_query(query, {"email": email.lower()})


def get_registered_user_by_username(db, username):
    query = """
        SELECT user_id, client_id, seller_id, email, username, hashed_password
        FROM registered_user
        WHERE username = %(username)s
    """
    return db.execute_query(query, {"username": username})


def get_registered_user_by_login(db, login):
    query = """
        SELECT user_id, client_id, seller_id, email, username, hashed_password
        FROM registered_user
        WHERE LOWER(email) = %(email)s OR username = %(username)s
    """
    return db.execute_query(query, {
        "email": login.lower(),
        "username": login
    })


def get_registered_user_by_id(db, user_id):
    query = """
        SELECT user_id, client_id, seller_id, email, username, hashed_password
        FROM registered_user
        WHERE user_id = %(user_id)s
    """
    return db.execute_query(query, {"user_id": str(user_id)})


def insert_registered_user(db, client_id, seller_id, email, username, hashed_password):
    query = """
        INSERT INTO registered_user (
            client_id,
            seller_id,
            email,
            username,
            hashed_password
        )
        VALUES (
            %(client_id)s,
            %(seller_id)s,
            %(email)s,
            %(username)s,
            %(hashed_password)s
        )
        RETURNING user_id, client_id, seller_id, email, username
    """
    return db.execute_insert_update_delete(query, {
        "client_id": str(client_id),
        "seller_id": str(seller_id),
        "email": email.lower(),
        "username": username,
        "hashed_password": hashed_password
    })