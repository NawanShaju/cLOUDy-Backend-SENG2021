from flask import Blueprint, jsonify, request, Response
from app.services.order_service import create_order_v2_service
from app.utils.xml_generation import generate_xml_v2
from .services.validate_order import validate_order
from .services.api_key import validate_api_key, validate_buyer_auth
from .services.db_services.xml_db import xml_to_db
from .utils.helper import is_valid_uuid, to_iso_date
from database.PostgresDB import PostgresDB
from app.utils.extensions import limiter
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

api = Blueprint("v2", __name__)

@api.route("/v2/seller/<sellerId>/cart", methods=["GET"])
@validate_api_key
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
@limiter.limit("60 per minute")
def get_seller_products(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = get_products_for_seller_service(db, sellerId)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "sellerId": sellerId,
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
 