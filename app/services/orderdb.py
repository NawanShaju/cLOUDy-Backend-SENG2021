from flask import jsonify
from database.PostgresDB import PostgresDB

def create_order_db(data, buyerId):
    
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400

    db = PostgresDB()
    

    address_id = insert_address(data.get("address"))
    product_ids = insert_product(data.get("items"))
    
    order_id = insert_order(data, buyerId, address_id)
    
    insert_order_item(data.get("items"), order_id, product_ids)
    
    return order_id
    
def insert_order_item(items, order_id, product_ids):
    
    db = PostgresDB()

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
    """

    for item, product_id in zip(items, product_ids):
        params = {
            "order_id": order_id,
            "product_id": product_id,
            "quantity": item.get("quantity"),
            "total_price": item.get("unit_price") * item.get("quantity")
        }

        db.execute_insert_update_delete(query, params)
    
    
def insert_order(data, buyerId, address_id):
    db = PostgresDB()
    
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
    
    params = []
    status = "CREATED"
    params.append(buyerId)
    params.append(address_id)
    params.append(data.get("order_date"))
    params.append(data.get("delivery_date"))
    params.append(data.get("currency_code"))
    params.append(status)
    
    return db.execute_insert_update_delete(query, params)

def insert_product(items):
    db = PostgresDB()
    
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
        RETURNING product_id
    """
    
    product_ids = []

    for item in items:
        result = db.execute_insert_update_delete(query, item, True)
        product_ids.append(result[0])

    return product_ids
    

def insert_address(address):
    
    db = PostgresDB()
    
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
        RETURNING address_id
    """
    
    params = []
    for fields in address:
        params.append(address.get(fields))
        
        
    return db.execute_insert_update_delete(query, params)