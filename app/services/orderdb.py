from flask import jsonify
from database.PostgresDB import PostgresDB

def create_order_db(data, buyerId):
    
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400

    db = PostgresDB()
    
    address_id = insert_address(db, data.get("address"))
    product_ids = insert_product(db, data.get("items"))
    
    order_id = insert_order(db, data, buyerId, address_id[0][0])
    
    insert_order_item(db, data.get("items"), order_id[0][0], product_ids[0])
    
    return order_id
    
def insert_order_item(db, items, order_id, product_ids):

    query = """
        INSERT INTO order_items (
            order_id,
            product_id,
            quantity,
            total_price
        ) 
        VALUES (
            %(order_id)s,
            %(product_id)s,
            %(quantity)s,
            %(total_price)s
        )
        ON CONFLICT (order_id, product_id)
        DO NOTHING
    """

    for item, product_id in zip(items, product_ids):
        params = {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": item.get("quantity"),
            "total_price": item.get("unit_price") * item.get("quantity")
        }

        db.execute_insert_update_delete(query, params)
    
    
def insert_order(db, data, buyerId, address_id):
    
    query = """
        INSERT INTO orders (
            external_buyer_id,
            address_id,
            order_date,
            delivery_date,
            currency_code,
            status
        ) 
        VALUES (
            %(buyerId)s,
            %(address_id)s,
            %(order_date)s,
            %(delivery_date)s,
            %(currency_code)s,
            %(status)s
        )
        RETURNING order_id
    """
    
    params = {
        "buyerId": buyerId,
        "address_id": address_id,
        "order_date": data.get("order_date"),
        "delivery_date": data.get("delivery_date"),
        "currency_code": data.get("currency_code"),
        "status": "CREATED"
    }
    
    return db.execute_insert_update_delete(query, params)

def insert_product(db, items):
    
    query = """
        INSERT INTO products (
            product_name,
            product_description,
            unit_price
        ) 
        VALUES (
            %(item_name)s,
            %(item_description)s,
            %(unit_price)s
        )
        ON CONFLICT (product_name, unit_price)
        DO UPDATE SET
            product_name = EXCLUDED.product_name
        RETURNING product_id
    """
    
    product_ids = []
    

    for item in items:
        result = db.execute_insert_update_delete(query, item)
        product_ids.append(result[0])

    return product_ids
    

def insert_address(db, address):
    
    query = """
        INSERT INTO addresses (
            street,
            city,
            state,
            postal_code,
            country_code
        )
        VALUES (
            %(street)s,
            %(city)s,
            %(state)s,
            %(postal_code)s,
            %(country_code)s
        )
        ON CONFLICT (street, city, state, postal_code, country_code)
        DO UPDATE SET
            street = EXCLUDED.street
        RETURNING address_id
    """
        
    return db.execute_insert_update_delete(query, address)