def insert_seller_despatch(db, seller_id, advice_id, order_id=None):
    if order_id:
        check_query = """
            SELECT id FROM seller_despatch
            WHERE order_id = %(order_id)s
        """
        existing = db.execute_query(check_query, {"order_id": str(order_id)})
        if existing:
            return None

    query = """
        INSERT INTO seller_despatch (seller_id, advice_id, order_id)
        VALUES (%(seller_id)s, %(advice_id)s, %(order_id)s)
        ON CONFLICT (seller_id, advice_id) DO NOTHING
        RETURNING id
    """
    return db.execute_insert_update_delete(query, {
        "seller_id": str(seller_id),
        "advice_id": str(advice_id),
        "order_id":  str(order_id) if order_id else None,
    })


def get_advice_ids_for_seller(db, seller_id):
    query = """
        SELECT advice_id FROM seller_despatch
        WHERE seller_id = %(seller_id)s
    """
    rows = db.execute_query(query, {"seller_id": str(seller_id)}, fetch_all=True)
    return {row[0] for row in (rows or [])}


def get_order_id_for_advice(db, advice_id):
    query = """
        SELECT order_id FROM seller_despatch
        WHERE advice_id = %(advice_id)s
    """
    row = db.execute_query(query, {"advice_id": str(advice_id)})
    return str(row[0]) if row else None