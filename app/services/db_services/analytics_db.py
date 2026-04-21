def get_total_orders_by_seller(db, seller_id):
    query = """
        SELECT COUNT(*)
        FROM orders
        WHERE seller_id = %(seller_id)s
    """
    return db.execute_query(query, {"seller_id": str(seller_id)})


def get_total_revenue_by_seller(db, seller_id):
    query = """
        SELECT COALESCE(SUM(oi.total_price), 0)
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.seller_id = %(seller_id)s
          AND COALESCE(o.status, '') != 'CANCELED'
    """
    return db.execute_query(query, {"seller_id": str(seller_id)})


def get_repeat_buyers_by_seller(db, seller_id):
    query = """
        SELECT COUNT(*)
        FROM (
            SELECT buyer_id
            FROM orders
            WHERE seller_id = %(seller_id)s
              AND buyer_id IS NOT NULL
            GROUP BY buyer_id
            HAVING COUNT(*) > 1
        ) AS repeat_buyers
    """
    return db.execute_query(query, {"seller_id": str(seller_id)})


def get_status_breakdown_by_seller(db, seller_id):
    query = """
        SELECT COALESCE(status, 'UNKNOWN') AS status, COUNT(*) AS count
        FROM orders
        WHERE seller_id = %(seller_id)s
        GROUP BY status
        ORDER BY count DESC
    """
    return db.execute_query(query, {"seller_id": str(seller_id)}, fetch_all=True)


def get_orders_by_date_for_seller(db, seller_id):
    query = """
        SELECT
            o.order_date::date AS order_day,
            COUNT(DISTINCT o.order_id) AS orders,
            COALESCE(SUM(
                CASE
                    WHEN COALESCE(o.status, '') != 'CANCELED'
                    THEN oi.total_price
                    ELSE 0
                END
            ), 0) AS revenue
        FROM orders o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.seller_id = %(seller_id)s
        GROUP BY order_day
        ORDER BY order_day ASC
    """
    return db.execute_query(query, {"seller_id": str(seller_id)}, fetch_all=True)


def get_top_products_by_seller(db, seller_id):
    query = """
        SELECT
            p.product_id,
            COALESCE(p.product_name, 'Unknown Product') AS product_name,
            COALESCE(SUM(oi.quantity), 0) AS total_quantity,
            COALESCE(SUM(
                CASE
                    WHEN COALESCE(o.status, '') != 'CANCELED'
                    THEN oi.total_price
                    ELSE 0
                END
            ), 0) AS total_revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.product_id
        WHERE o.seller_id = %(seller_id)s
        GROUP BY p.product_id, p.product_name
        ORDER BY total_quantity DESC, total_revenue DESC
        LIMIT 5
    """
    return db.execute_query(query, {"seller_id": str(seller_id)}, fetch_all=True)


def get_top_buyers_by_seller(db, seller_id):
    query = """
        SELECT
            b.buyer_id,
            COALESCE(b.party_name, 'Unknown Buyer') AS buyer_name,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(
                CASE
                    WHEN COALESCE(o.status, '') != 'CANCELED'
                    THEN oi.total_price
                    ELSE 0
                END
            ), 0) AS total_spend
        FROM orders o
        LEFT JOIN buyers b ON o.buyer_id = b.buyer_id
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.seller_id = %(seller_id)s
        GROUP BY b.buyer_id, b.party_name
        ORDER BY total_spend DESC, total_orders DESC
        LIMIT 5
    """
    return db.execute_query(query, {"seller_id": str(seller_id)}, fetch_all=True)