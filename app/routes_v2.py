from flask import Blueprint, jsonify, request, Response
from app.services.db_services.despatch_db import get_advice_ids_for_seller, get_order_id_for_advice, insert_seller_despatch
from app.services.db_services.order_db import get_order_details, get_order_by_id
from app.services.order_service import create_order_v2_service
from app.utils.xml_generation import generate_xml_v2
from .services.validate_order import validate_order
from .services.api_key import validate_api_key, validate_buyer_auth
from .services.db_services.xml_db import xml_to_db
from .utils.helper import is_valid_uuid, parse_date, to_iso_date
from database.PostgresDB import PostgresDB
from app.utils.extensions import limiter
from app.services.api_key import validate_seller_auth
from app.services.product_service import (
    create_product_service,
    update_product_service,
    delete_product_service,
    get_products_for_seller_service,
    get_product_by_id_service,
)
from app.services.cart_service import (
    get_cart_service,
    add_to_cart_service,
    update_cart_item_service,
    remove_from_cart_service,
    clear_cart_service,
    checkout_service,
)
from app.services.inventory_service import (
    create_inventory_service,
    update_inventory_service,
    delete_inventory_service,
    get_inventory_service,
)

api = Blueprint("v2", __name__)

@api.route("/v2/seller/<sellerId>/cart", methods=["GET"])
@validate_api_key
@validate_seller_auth
@limiter.limit("60 per minute")
def get_cart(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = get_cart_service(db, sellerId)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 200


@api.route("/v2/seller/<sellerId>/cart/item", methods=["POST"])
@validate_api_key
@validate_seller_auth
@limiter.limit("30 per minute")
def add_to_cart(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON provided"}), 400

    product_id = data.get("product_id")
    if product_id and not is_valid_uuid(product_id):
        return jsonify({"error": "product_id must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = add_to_cart_service(db, sellerId, data)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 200


@api.route("/v2/seller/<sellerId>/cart/item/<productId>", methods=["PUT"])
@validate_api_key
@validate_seller_auth
@limiter.limit("30 per minute")
def update_cart_item(sellerId, productId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400
    if not is_valid_uuid(productId):
        return jsonify({"error": "productId must be a valid UUID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON provided"}), 400

    with PostgresDB() as db:
        result = update_cart_item_service(db, sellerId, productId, data)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 200


@api.route("/v2/seller/<sellerId>/cart/item/<productId>", methods=["DELETE"])
@validate_api_key
@validate_seller_auth
@limiter.limit("30 per minute")
def remove_from_cart(sellerId, productId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400
    if not is_valid_uuid(productId):
        return jsonify({"error": "productId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = remove_from_cart_service(db, sellerId, productId)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 200


@api.route("/v2/seller/<sellerId>/cart", methods=["DELETE"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def clear_cart_route(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = clear_cart_service(db, sellerId)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 200


@api.route("/v2/seller/<sellerId>/cart/checkout", methods=["POST"])
@validate_api_key
@validate_seller_auth
@limiter.limit("10 per minute")
def checkout(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON provided"}), 400

    buyer_id = data.get("buyer_id")
    if not buyer_id:
        return jsonify({"error": "buyer_id is required"}), 400
    if not is_valid_uuid(buyer_id):
        return jsonify({"error": "buyer_id must be a valid UUID"}), 400

    if data.get("delivery_date"):
        data["delivery_date"] = to_iso_date(data["delivery_date"])

    api_key = request.headers.get("api-key")

    with PostgresDB() as db:
        result = checkout_service(db, sellerId, buyer_id, data, api_key)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 200

@api.route("/v2/seller/<sellerId>/product", methods=["POST"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def create_product(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON provided"}), 400

    with PostgresDB() as db:
        result = create_product_service(db, sellerId, data)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "productId": result["product_id"],
        "message": "Product created successfully"
    }), 201


@api.route("/v2/seller/<sellerId>/product/<productId>", methods=["PUT"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def update_product(sellerId, productId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400
    if not is_valid_uuid(productId):
        return jsonify({"error": "productId must be a valid UUID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON provided"}), 400

    with PostgresDB() as db:
        result = update_product_service(db, productId, sellerId, data)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "productId": result["product_id"],
        "message":   result["message"]
    }), 200


@api.route("/v2/seller/<sellerId>/product/<productId>", methods=["DELETE"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def delete_product(sellerId, productId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400
    if not is_valid_uuid(productId):
        return jsonify({"error": "productId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = delete_product_service(db, productId, sellerId)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "productId": result["product_id"],
        "message":   result["message"]
    }), 200


@api.route("/v2/seller/<sellerId>/products", methods=["GET"])
@validate_api_key
@validate_seller_auth
@limiter.limit("60 per minute")
def get_seller_products(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    product_type = request.args.get("type")

    if product_type and product_type not in ["catalogue", "inventory"]:
        return jsonify({"error": "Invalid product type"}), 400

    with PostgresDB() as db:
        result = get_products_for_seller_service(db, sellerId)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "sellerId": sellerId,
        "type":     product_type,
        "count":    len(result),
        "products": result
    }), 200


@api.route("/v2/product/<productId>", methods=["GET"])
@validate_api_key
@limiter.limit("60 per minute")
def get_product(productId):
    if not is_valid_uuid(productId):
        return jsonify({"error": "productId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = get_product_by_id_service(db, productId)

    if not result:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(result), 200


@api.route("/v2/buyer/<buyerId>/order", methods=["POST"])
@validate_api_key
@validate_buyer_auth
@limiter.limit("10 per minute")
def create_order_v2(buyerId):
    if not is_valid_uuid(buyerId):
        return jsonify({"error": "buyerId must be a valid UUID"}), 400
    
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400

    if data.get("order_date"):
        data["order_date"] = to_iso_date(data.get("order_date"))

    if data.get("delivery_date"):
        data["delivery_date"] = to_iso_date(data.get("delivery_date"))

    seller_id = data.get("seller_id")
    if seller_id and not is_valid_uuid(seller_id):
        return jsonify({"error": "seller_id must be a valid UUID"}), 400
 
    validate_error = validate_order(data, buyerId)
    if validate_error:
        return jsonify({"error": validate_error}), 400

    with PostgresDB() as db:
        result = create_order_v2_service(db, data, buyerId)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

        order_id = result["order_id"]
        buyer_data = result["buyer_data"]
        seller_data = result["seller_data"]
 
        xml_string = generate_xml_v2(data, order_id, buyerId, buyer_data, seller_data)
        xml_to_db(db, xml_string, order_id)
 
        return Response(xml_string, mimetype="application/xml", status=200)

@api.route("/v2/seller/<sellerId>/inventory", methods=["GET"])
@validate_api_key
@validate_seller_auth
@limiter.limit("60 per minute")
def get_inventory(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400
    
    with PostgresDB() as db:
        result = get_inventory_service(db, sellerId)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
    
    return jsonify(result), 200


@api.route("/v2/seller/<sellerId>/inventory", methods=["POST"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def create_inventory_item(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid JSON provided"}), 400
    
    with PostgresDB() as db:
        result = create_inventory_service(db, sellerId, data)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
    
    return jsonify(result), 201


@api.route("/v2/seller/<sellerId>/inventory/<inventoryId>", methods=["PUT"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def update_inventory_item_route(sellerId, inventoryId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400
    
    if not is_valid_uuid(inventoryId):
        return jsonify({"error": "inventoryId must be a valid UUID"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid JSON provided"}), 400
    
    with PostgresDB() as db:
        result = update_inventory_service(db, sellerId, inventoryId, data)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
    
    return jsonify(result), 200


@api.route("/v2/seller/<sellerId>/inventory/<inventoryId>", methods=["DELETE"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def delete_inventory_item_route(sellerId, inventoryId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400
    
    if not is_valid_uuid(inventoryId):
        return jsonify({"error": "inventoryId must be a valid UUID"}), 400
    
    with PostgresDB() as db:
        result = delete_inventory_service(db, sellerId, inventoryId)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
    
    return jsonify(result), 200

@api.route("/v2/seller/<sellerId>/despatch", methods=["POST"])
@validate_api_key
def link_despatch(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON provided"}), 400

    advice_id = data.get("advice_id")
    order_id  = data.get("order_id")

    if not advice_id:
        return jsonify({"error": "advice_id is required"}), 400

    with PostgresDB() as db:
        insert_seller_despatch(db, sellerId, advice_id, order_id)

    return jsonify({"message": "Despatch linked successfully"}), 201


@api.route("/v2/seller/<sellerId>/despatch", methods=["GET"])
@validate_api_key
def get_seller_despatch_ids(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    with PostgresDB() as db:
        advice_ids = get_advice_ids_for_seller(db, sellerId)

    return jsonify({"adviceIds": list(advice_ids)}), 200

@api.route("/v2/seller/<sellerId>/despatch/<adviceId>/order", methods=["GET"])
@validate_api_key
def get_order_for_despatch(sellerId, adviceId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400
    if not is_valid_uuid(adviceId):
        return jsonify({"error": "adviceId must be a valid UUID"}), 400

    with PostgresDB() as db:
        order_id = get_order_id_for_advice(db, adviceId)
        if not order_id:
            return jsonify({"error": "No order linked to this despatch"}), 404

        order_row = get_order_by_id(db, order_id, order_id)
        if not order_row:
            return jsonify({"error": "Order not found"}), 404

        buyer_id = str(order_row[0][9]) if order_row[0][9] else str(order_row[0][2])
        results = get_order_details(db, buyer_id, order_id)
        
    if not results:
        return jsonify({"error": "Order details not found"}), 404
    
    return jsonify({
        "orderId":      str(results[0][0]),
        "status":       results[0][1],
        "orderDate":    parse_date(order_row[0][4]),
        "currencyCode": order_row[0][5],
        "deliveryDate": parse_date(order_row[0][7]),
        "items": [
            {
                "productId":          str(row[2]) if row[2] else None,
                "productName":        row[3],
                "productDescription": row[4],
                "unitPrice":          str(row[5]) if row[5] else None,
                "quantity":           row[6],
                "totalPrice":         str(row[7]) if row[7] else None,
            }
            for row in results
        ]
    }), 200