from app.services.db_services.analytics_db import (
    get_total_orders_by_seller,
    get_total_revenue_by_seller,
    get_repeat_buyers_by_seller,
    get_status_breakdown_by_seller,
    get_orders_by_date_for_seller,
    get_top_products_by_seller,
    get_top_buyers_by_seller,
)


def get_seller_analytics_service(db, seller_id):
    total_orders_row = get_total_orders_by_seller(db, seller_id)
    total_revenue_row = get_total_revenue_by_seller(db, seller_id)
    repeat_buyers_row = get_repeat_buyers_by_seller(db, seller_id)

    status_rows = get_status_breakdown_by_seller(db, seller_id) or []
    orders_by_date_rows = get_orders_by_date_for_seller(db, seller_id) or []
    top_products_rows = get_top_products_by_seller(db, seller_id) or []
    top_buyers_rows = get_top_buyers_by_seller(db, seller_id) or []

    total_orders = total_orders_row[0] if total_orders_row else 0
    total_revenue = float(total_revenue_row[0]) if total_revenue_row and total_revenue_row[0] is not None else 0.0
    repeat_buyers = repeat_buyers_row[0] if repeat_buyers_row else 0

    average_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    status_breakdown = [
        {
            "status": row[0],
            "count": row[1]
        }
        for row in status_rows
    ]

    orders_by_date = [
        {
            "date": row[0].isoformat() if row[0] else None,
            "orders": row[1],
            "revenue": float(row[2]) if row[2] is not None else 0.0
        }
        for row in orders_by_date_rows
    ]

    top_products = [
        {
            "productId": str(row[0]) if row[0] is not None else None,
            "itemName": row[1],
            "totalQuantity": row[2],
            "totalRevenue": float(row[3]) if row[3] is not None else 0.0
        }
        for row in top_products_rows
    ]

    top_buyers = [
        {
            "buyerId": str(row[0]) if row[0] is not None else None,
            "buyerName": row[1],
            "totalOrders": row[2],
            "totalSpend": float(row[3]) if row[3] is not None else 0.0
        }
        for row in top_buyers_rows
    ]

    return {
        "sellerId": str(seller_id),
        "summary": {
            "totalOrders": total_orders,
            "totalRevenue": total_revenue,
            "averageOrderValue": average_order_value,
            "repeatBuyers": repeat_buyers
        },
        "statusBreakdown": status_breakdown,
        "ordersByDate": orders_by_date,
        "topProducts": top_products,
        "topBuyers": top_buyers
    }