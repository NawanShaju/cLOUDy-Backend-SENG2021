def insert_seller_auth(db, api_key, seller_id):
    query = """
        INSERT INTO seller_auth (api_key, seller_id)
        VALUES (%(api_key)s, %(seller_id)s)
        ON CONFLICT (api_key, seller_id) DO NOTHING
    """

    db.execute_insert_update_delete(query, {
        "api_key": api_key,
        "seller_id": str(seller_id)
    })

def get_seller_id_by_api_key(db, api_key):
    query = """
        SELECT seller_id
        FROM seller_auth
        WHERE api_key = %(api_key)s
        LIMIT 1
    """
    return db.execute_query(query, {"api_key": api_key})