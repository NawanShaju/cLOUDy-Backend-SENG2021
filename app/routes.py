from flask import Blueprint, jsonify, request, Response
from app.services.buyer_service import (
    create_buyer_service,
    update_buyer_service,
    delete_buyer_service,
    get_buyers_for_seller_service,
    create_buyer_seller_service,
    delete_buyer_seller_service
)
from app.services.seller_service import (
    create_seller_service,
    update_seller_service,
    delete_seller_service
)
from app.services.db_services.seller_db import get_seller_by_id
from app.services.auth_services import register_auth_service, login_auth_service
from app.services.app_auth_service import (
    register_app_user_service,
    login_app_user_service,
)
from .services.api_key import validate_api_key
from app.services.db_services.buyer_db import get_buyer_by_id
from app.services.app_auth_service import (
    register_app_user_service,
    login_app_user_service,
)
from .services.validate_order import validate_order, validate_order_xml
from .services.api_key import validate_api_key, validate_buyer_auth
from .services.db_services.seller_db import get_all_sellers
from .services.db_services.buyer_db import get_buyers_by_api_key
from app.services.api_key import validate_seller_auth
from .utils.xml_generation import generate_xml, generate_xml_v2
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
from .services.product_service import get_products_by_api_key_service, get_products_for_seller_service
from .services.db_services.xml_db import xml_to_db_update_cancel
from app.services.analytics_service import get_seller_analytics_service
from .services.email.email_services import send_email
from .utils.helper import parse_email_request, to_iso_date
from app.utils.helper import is_valid_uuid
from database.PostgresDB import PostgresDB
from flask import send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from app.utils.extensions import limiter
from app.utils.helper import is_json
from app.ai_model.model import extract_order_full
import cloudinary.uploader
import os

api = Blueprint("v1", __name__)

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

@api.route("/v1/auth/register", methods=["POST"])
@validate_api_key
@limiter.limit("20 per minute")
def register_auth():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400

    api_key = request.headers.get("api-key")

    with PostgresDB() as db:
        result = register_app_user_service(db, data, api_key)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 201


@api.route("/v1/auth/login", methods=["POST"])
@validate_api_key
@limiter.limit("30 per minute")
def login_auth():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400

    api_key = request.headers.get("api-key")

    with PostgresDB() as db:
        result = login_app_user_service(db, data, api_key)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 200

@api.route("/v1/buyer/<buyerId>/order", methods=["POST"])
@validate_api_key
@limiter.limit("10 per minute")
def create_order(buyerId):
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
        
    if data.get("order_date"):
        data["order_date"] = to_iso_date(data.get("order_date"))
    
    if data.get("delivery_date"):
        data["delivery_date"] = to_iso_date(data.get("delivery_date"))
    
    validate_error = validate_order(data, buyerId)
    
    if validate_error:
        return jsonify({"error": validate_error}), 400
    
    api_key = request.headers.get("api-key")

    with PostgresDB() as db:
        order_id = create_order_service(db, data, buyerId, api_key)
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

@api.route("/v1/buyer", methods=["POST"])
@validate_api_key
@limiter.limit("20 per minute")
def create_buyer():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
    
    api_key = request.headers.get("api-key")

    with PostgresDB() as db:
        result = create_buyer_service(db, data, api_key)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "buyerId": result["buyer_id"],
        "message": "Buyer created successfully"
    }), 201

@api.route("/v1/buyer/<buyerId>", methods=["PUT"])
@validate_api_key
@limiter.limit("20 per minute")
def update_buyer(buyerId):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400

    if not is_valid_uuid(buyerId):
        return jsonify({"error": "buyerId must be a valid UUID"}), 400

    api_key = request.headers.get("api-key")

    with PostgresDB() as db:
        result = update_buyer_service(db, buyerId, data, api_key)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "buyerId": result["buyer_id"],
        "message": result["message"]
    }), 200

@api.route("/v1/buyer/<buyerId>", methods=["DELETE"])
@validate_api_key
@limiter.limit("20 per minute")
def delete_buyer(buyerId):
    if not is_valid_uuid(buyerId):
        return jsonify({"error": "buyerId must be a valid UUID"}), 400

    api_key = request.headers.get("api-key")

    with PostgresDB() as db:
        result = delete_buyer_service(db, buyerId, api_key)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "buyerId": result["buyer_id"],
        "message": result["message"]
    }), 200   

@api.route("/v1/seller", methods=["POST"])
@validate_api_key
@limiter.limit("20 per minute")
def create_seller():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
 
    with PostgresDB() as db:
        result = create_seller_service(db, data)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
 
        return jsonify({
            "sellerId": result["seller_id"],
            "message": "Seller created successfully"
        }), 201

@api.route("/v1/seller/<sellerId>", methods=["PUT"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def update_seller(sellerId):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400

    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = update_seller_service(db, sellerId, data)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "sellerId": result["seller_id"],
        "message": result["message"]
    }), 200

@api.route("/v1/seller/<sellerId>", methods=["DELETE"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def delete_seller(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = delete_seller_service(db, sellerId)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "sellerId": result["seller_id"],
        "message": result["message"]
    }), 200

@api.route("/v1/buyer/<buyerId>/order/<orderId>", methods=["PUT"])
@validate_api_key
@validate_buyer_auth
@limiter.limit("100 per hour")
def update_order(buyerId, orderId):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
    
    if not is_valid_uuid(orderId):
        return jsonify({"error": "orderId must be a valid UUID"}), 400
    
    if not is_valid_uuid(buyerId):
        return jsonify({"error": "buyerId must be a valid UUID"}), 400
    
    seller_id = data.get("seller_id")
    if seller_id and not is_valid_uuid(seller_id):
        return jsonify({"error": "seller_id must be a valid UUID"}), 400
    
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
        if not full_order:
            return jsonify({"error": "Order not found"}), 404
 
        buyer_data  = None
        seller_data = None
 
        try:
            buyer_data = get_buyer_by_id(db, buyerId)
        except Exception:
            pass
 
        if buyer_data and seller_id:
            try:
                seller_data = get_seller_by_id(db, seller_id)
            except Exception:
                pass
 
        if buyer_data:
            xml_string = generate_xml_v2(full_order, orderId, buyerId, buyer_data, seller_data)
        else:
            xml_string = generate_xml(full_order, orderId, buyerId)
 
        xml_to_db_update_cancel(db, xml_string, orderId)
 
        return Response(xml_string, mimetype="application/xml", status=200)


@api.route("/v1/buyer/<buyerId>/order/<orderId>", methods = ["GET"])
@validate_api_key
@validate_buyer_auth
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
@validate_buyer_auth
@limiter.limit("20 per minute")
def cancel_order(buyerId, orderId):
    if not is_valid_uuid(orderId):
        return jsonify({"error": "orderId must be a valid UUID"}), 400
    
    with PostgresDB() as db:
        result = cancel_order_service(db, buyerId, orderId)

    if result.get("status") != 200 and result.get("status") != 'CANCELED':
        return jsonify(result), result.get("status")

    return jsonify(result), 200

@api.route("/v1/buyer/<buyerId>/order/<orderId>", methods=["DELETE"])
@validate_api_key
@validate_buyer_auth
@limiter.limit("20 per minute")
def delete_order_by_id(buyerId, orderId):
    if not is_valid_uuid(orderId):
        return jsonify({"error": "orderId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = delete_order_service(db, buyerId, orderId)

    if result.get("status") != 200:
        return jsonify(result), result.get("status")

    return jsonify(result), 200

@api.route("/v1/buyer/<buyerId>/order", methods = ["GET"])
@validate_api_key
@validate_buyer_auth
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
            orders = []
        
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
    
@api.route("/v1/buyers", methods=["GET"])
@validate_api_key
@limiter.limit("60 per minute")
def get_all_buyers():
    api_key = request.headers.get("api-key")

    with PostgresDB() as db:
        buyers = get_buyers_by_api_key(db, api_key)

    if not buyers:
        return jsonify({"buyers": []}), 200

    return jsonify({
        "buyers": [
            {
                "buyerId": str(row[0]),
                "party_name": row[1],
                "customer_assigned_account_id": row[2],
                "contact_name": row[3],
                "contact_email": row[4]
            }
            for row in buyers
        ]
    }), 200

@api.route("/v1/sellers", methods=["GET"])
@validate_api_key
@limiter.limit("60 per minute")
def get_all_sellers_route():
    
    api_key = request.headers.get("api-key")
    
    with PostgresDB() as db:
        sellers = get_all_sellers(db, api_key)

    if sellers is None:
        return jsonify({"error": "Invalid API key"}), 401

    if not sellers:
        return jsonify({"sellers": []}), 200

    return jsonify({
        "sellers": [
            {
                "seller_id": str(row[0]),
                "party_name": row[1],
                "customer_assigned_account_id": row[2]
            }
            for row in sellers
        ]
    }), 200

@api.route("/v1/buyer/<buyerId>/order/CANCELED", methods=["DELETE"])
@validate_api_key
@validate_buyer_auth
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

@api.route("/v1/seller/<sellerId>/buyers", methods=["GET"])
@validate_api_key
@validate_seller_auth
@limiter.limit("60 per minute")
def get_buyers_for_seller(sellerId):

    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    with PostgresDB() as db:
        buyers = get_buyers_for_seller_service(db, sellerId)

    return jsonify(buyers), 200
    
@api.route("/v1/seller/<sellerId>/buyers/<buyerId>", methods=["POST"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def create_buyer_seller(sellerId, buyerId):
    if not buyerId or not is_valid_uuid(buyerId):
        return jsonify({"error": "Valid buyer_id is required"}), 400

    if not sellerId or not is_valid_uuid(sellerId):
        return jsonify({"error": "Valid seller_id is required"}), 400

    with PostgresDB() as db:
        result = create_buyer_seller_service(db, buyerId, sellerId)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 201

@api.route("/v1/seller/<sellerId>/buyers/<buyerId>", methods=["DELETE"])
@validate_api_key
@validate_seller_auth
@limiter.limit("20 per minute")
def delete_buyer_seller(sellerId, buyerId):
    if not buyerId or not is_valid_uuid(buyerId):
        return jsonify({"error": "Valid buyer_id is required"}), 400

    if not sellerId or not is_valid_uuid(sellerId):
        return jsonify({"error": "Valid seller_id is required"}), 400

    with PostgresDB() as db:
        result = delete_buyer_seller_service(db, buyerId, sellerId)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify(result), 200

@api.route("/v1/seller/<sellerId>/analytics/dashboard", methods=["GET"])
@validate_api_key
@validate_seller_auth
@limiter.limit("60 per minute")
def get_seller_analytics_dashboard(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    try:
        with PostgresDB() as db:
            result = get_seller_analytics_service(db, sellerId)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to fetch seller analytics dashboard",
            "details": str(e)
        }), 500

@api.route("/extract-order", methods=["POST"])
@validate_api_key
def extract_order():
    data = request.get_json()
    text = data.get("text")
    seller_id = data.get("seller_id")
    
    if not text:
        return jsonify({"error": "Missing text"}), 400

    if not seller_id:
        return jsonify({"error": "Missing sellerId"}), 400

    result = extract_order_full(text, seller_id)

    return jsonify(result)

@api.route("/v1/public/seller/<sellerId>/products", methods=["GET"])
@validate_api_key
@limiter.limit("60 per minute")
def get_public_seller_products_route(sellerId):
    if not is_valid_uuid(sellerId):
        return jsonify({"error": "sellerId must be a valid UUID"}), 400

    with PostgresDB() as db:
        result = get_products_for_seller_service(db, sellerId)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "sellerId": sellerId,
        "count": len(result),
        "products": result
    }), 200

@api.route("/v1/products", methods=["GET"])
@validate_api_key
@limiter.limit("60 per minute")
def get_products_by_api_key():
    api_key = request.headers.get("api-key")

    with PostgresDB() as db:
        result = get_products_by_api_key_service(db, api_key)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

    return jsonify({
        "count": len(result),
        "products": result
    }), 200
    
@api.route('/v1/upload-image', methods=['POST'])
@validate_api_key
def upload_image():
    file = request.files.get('file')

    product_id = request.form.get('product_id')
    inventory_id = request.form.get('inventory_id')

    if not file:
        return jsonify({"error": "No file provided"}), 400

    if not product_id and not inventory_id:
        return jsonify({"error": "Must provide product_id or inventory_id"}), 400

    if product_id and inventory_id:
        return jsonify({"error": "Provide only one of product_id or inventory_id"}), 400

    result = cloudinary.uploader.upload(file)
    image_url = result['secure_url']

    with PostgresDB() as db:
        if product_id:
            db.execute_insert_update_delete("""
                UPDATE products
                SET image_url = %s
                WHERE product_id = %s
            """, (image_url, product_id))

        elif inventory_id:
            db.execute_insert_update_delete("""
                UPDATE inventory
                SET image_url = %s
                WHERE inventory_id = %s
            """, (image_url, inventory_id))

    return jsonify({
        "url": image_url,
        "product_id": product_id,
        "inventory_id": inventory_id
    })

@api.route("/send-email", methods=["POST"])
def send_email_route():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "Request body must be valid JSON."}), 400
 
    payload, error = parse_email_request(data)
    if error:
        return jsonify({"success": False, "message": error}), 422
 
    result = send_email(payload)
    status_code = 200 if result["success"] else 500
    return jsonify(result), status_code

def register_swagger_yaml(app):
    @app.route("/swagger.yaml")
    @limiter.limit("100 per minute")
    def swagger_spec():
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return send_from_directory(parent_dir, "swagger.yaml")
