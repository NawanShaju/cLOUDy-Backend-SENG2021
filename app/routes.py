from flask import Blueprint, jsonify, request, Response
from .services.validate_order import validate_order
from .services.xmlGeneraiton import generate_xml
from .services.orderdb import create_order_db
from .services.xmldb import xml_to_db
from .utils.helper import to_iso_date
from .services.orderdb import update_order_service
from .services.orderdb import delete_order_service
from database.PostgresDB import PostgresDB

api = Blueprint("main", __name__)

@api.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "running"}), 200

@api.route("v1/buyer/<buyerId>/order", methods=["POST"])
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
        order_id = create_order_db(db, data, buyerId)
        xml_string = generate_xml(data, order_id[0][0], buyerId)
        xml_to_db(db, xml_string, order_id[0][0])
    
    return Response(
        xml_string,
        mimetype='application/xml',
        status=200
    )


@api.route("/v1/buyer/<buyerId>/order/<orderId>", methods=["PUT"])
def update_order(buyerId, orderId):
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
    
    if data.get("order_date"):
        data["order_date"] = to_iso_date(data.get("order_date"))

    if data.get("delivery_date"):
        data["delivery_date"] = to_iso_date(data.get("delivery_date"))
    
    with PostgresDB() as db:
        results = update_order_service(db, buyerId, orderId, data)
    xml_string = None
    for result in results:
        if result.get("status") == 404:
            return jsonify(result), 404

        if result.get("status") == 500:
            return jsonify(result), 500

        xml_string = generate_xml(result)

    return Response(
        xml_string,
        mimetype='application/xml',
        status=200
    )


@api.route("/v1/buyer/<buyerId>/order/<orderId>", methods=["DELETE"])
def delete_order(buyerId, orderId):
    
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
