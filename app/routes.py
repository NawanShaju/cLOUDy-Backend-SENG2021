from flask import Blueprint, jsonify, request, Response
from .services.validate_order import validate_order, validate_order_xml
from .utils.xml_generation import generate_xml
from .services.api_key import validate_api_key
from .services.order_service import (
    get_full_order_service,
    create_order_service,
    update_order_service,
    cancel_order_service,
    delete_order_service,
    get_order_details_service,
    get_orders_for_buyer_service,
    delete_buyers_all_cancelled_orders_service
)
from .services.db_services.xml_db import xml_to_db
from .services.api_key import get_api_key
from .services.db_services.xml_db import xml_to_db_update_cancel
from .utils.helper import to_iso_date
from app.utils.helper import is_valid_uuid
from database.PostgresDB import PostgresDB
from flask import send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from app.utils.extensions import limiter
from app.utils.helper import is_json
import os

api = Blueprint("main", __name__)

SWAGGER_URL = "/swagger"
API_URL = "/swagger.yaml"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Order API"}
)

@api.route("/health", methods=["GET"])
@limiter.limit("200 per minute")
def health_check():
    return jsonify({"status": "running"}), 200

@api.route("/v1/buyer/<buyerId>/order", methods=["POST"])
@validate_api_key
@limiter.limit("10 per minute")
def create_order(buyerId):
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
        
    data["order_date"] = to_iso_date(data.get("order_date"))
    data["delivery_date"] = to_iso_date(data.get("delivery_date"))
    
    validate_error = validate_order(data, buyerId)
    
    if validate_error:
        return jsonify({"error": validate_error}), 400
    
    with PostgresDB() as db:
        order_id = create_order_service(db, data, buyerId)
        xml_string = generate_xml(data, order_id[0][0], buyerId)
        xml_to_db(db, xml_string, order_id[0][0])
    
    return Response(
        xml_string,
        mimetype='application/xml',
        status=200
    )
    
@api.route("/get-key", methods=["POST"])
@limiter.limit("100 per hour")
def create_apiKey():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid json Provided"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    api_key = None
    with PostgresDB() as db:
        try:
            api_key = get_api_key(db, username, password)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except PermissionError as e:
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 400
                
    return jsonify({
        "apikey": api_key
    })


@api.route("/v1/buyer/<buyerId>/order/<orderId>", methods=["PUT"])
@validate_api_key
@limiter.limit("100 per hour")
def update_order(buyerId, orderId):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
    
    if not is_valid_uuid(orderId):
        return jsonify({"error": "orderId must be a valid UUID"}), 400
    
    if data.get("order_date"):
        data["order_date"] = to_iso_date(data.get("order_date"))

    if data.get("delivery_date"):
        data["delivery_date"] = to_iso_date(data.get("delivery_date"))

    with PostgresDB() as db:
        result = update_order_service(db, data, buyerId, orderId)
        
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
    
        if not result:
            return jsonify({"error": "Order not found"}), 404
        
        full_order = get_full_order_service(db, buyerId, orderId)
        xml_string = generate_xml(full_order, orderId, buyerId)
        xml_to_db_update_cancel(db, xml_string, orderId)
    
    return Response(
        xml_string,
        mimetype='application/xml',
        status=200
    )


@api.route("/v1/buyer/<buyerId>/order/<orderId>", methods = ["GET"])
@validate_api_key
@limiter.limit("60 per minute")
def get_order_by_id(buyerId, orderId):
    if not is_valid_uuid(orderId):
        return jsonify({"error": "orderId must be a valid UUID"}), 400

    try:
        with PostgresDB() as db:
            order = get_order_details_service(db, buyerId, orderId) 
        if not order:
            return jsonify({
                "status": 404,
                "error": "Order couldnt be found"
            }), 404

        return jsonify(order), 200
    
    except Exception as e:
        return jsonify({
            "status": 500,
            "error": str(e)
        }), 500


@api.route("/v1/buyer/<buyerId>/order/<orderId>/CANCELED", methods=["DELETE"])
@validate_api_key
@limiter.limit("20 per minute")
def cancel_order(buyerId, orderId):
    if not is_valid_uuid(orderId):
        return jsonify({"error": "orderId must be a valid UUID"}), 400
    
    with PostgresDB() as db:
        result = cancel_order_service(db, buyerId, orderId)

    if result.get("status") == 401:
        return jsonify(result), 401
    
    if result.get("status") == 404:
        return jsonify(result), 404

    if result.get("status") == 403:
        return jsonify(result), 403

    if result.get("status") == 409:
        return jsonify(result), 409

    if result.get("status") == 500:
        return jsonify(result), 500

    return jsonify(result), 200

@api.route("/v1/buyer/<buyerId>/order/<orderId>", methods=["DELETE"])
@validate_api_key
@limiter.limit("20 per minute")
def delete_order_by_id(buyerId, orderId):
    if not is_valid_uuid(orderId):
        return jsonify({"error": "orderId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = delete_order_service(db, buyerId, orderId)

    if result.get("status") == 401:
        return jsonify(result), 401

    if result.get("status") == 404:
        return jsonify(result), 404

    if result.get("status") == 403:
        return jsonify(result), 403

    if result.get("status") == 409:
        return jsonify(result), 409

    if result.get("status") == 500:
        return jsonify(result), 500

    return jsonify(result), 200

@api.route("/v1/buyer/<buyerId>/order", methods = ["GET"])
@validate_api_key
@limiter.limit("60 per minute")
def get_orders_for_buyer(buyerId):
    try:
        status = request.args.get("status")
        from_date = request.args.get("fromDate")
        to_date = request.args.get("toDate")
        limit = request.args.get("limit", 10)
        offset = request.args.get("offset", 0)

        try:
            limit = int(limit)
            offset = int(offset)
        except ValueError:
            return jsonify({
                "status": 400,
                "error": "limit and offset must be integers"
            }), 400
        
        if limit <= 0 or offset < 0:
            return jsonify({
                "status": 400,
                "error": "limit must be greater than 0 and offset must be 0 or more"
            }), 400
        
        try:
            if from_date:
                from_date = to_iso_date(from_date)
            if to_date:
                to_date = to_iso_date(to_date)
        except ValueError as e:
            return jsonify({
                "status": 400,
                "error": str(e)
            }), 400
        
        with PostgresDB() as db:
            orders = get_orders_for_buyer_service(
                db,
                buyerId,
                status,
                from_date,
                to_date,
                limit,
                offset
            )

        if orders is None:
            return jsonify({
                "status": 404,
                "error": "Buyer not found"
            }), 404
        
        return jsonify({
            "status": 200,
            "message": "All orders for a buyer",
            "buyerId": buyerId,
            "count": len(orders),
            "limit": limit,
            "offset": offset,
            "orders": orders
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": 500,
            "error": str(e)
        }), 500


@api.route('/v1/validate-xml', methods=['POST'])
def validate_xml():
    try:
        xml_data = request.data.decode("utf-8")
        
        if not xml_data:
            return jsonify({"valid": False, "errors": ["Missing XML payload"]}), 400
        
        if is_json(xml_data):
            return jsonify({"valid": False, "error": ["Input must be XML"]})
        
        valid, errors = validate_order_xml(xml_data)

        return jsonify({"valid": valid, "errors": errors}), 200 if valid else 400

    except Exception as e:
        return jsonify({"valid": False, "errors": [str(e)]}), 500
    

@api.route("/v1/buyer/<buyerId>/order/CANCELED", methods=["DELETE"])
@validate_api_key
@limiter.limit("20 per minute")
def delete_cancelled_orders(buyerId):
    with PostgresDB() as db:
        result = delete_buyers_all_cancelled_orders_service(db, buyerId)
   
    if result.get("status") != 200:
        return jsonify(result), result.get("status")

    return jsonify({
        "buyerId": buyerId,
        "message": "All canceled orders deleted successfully"
    }), 200


def register_swagger_yaml(app):
    @app.route("/swagger.yaml")
    @limiter.limit("100 per minute")
    def swagger_spec():
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return send_from_directory(parent_dir, "swagger.yaml")
