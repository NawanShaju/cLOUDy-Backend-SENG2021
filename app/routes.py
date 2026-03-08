from flask import Blueprint, jsonify, request, Response
from .services.validate_order import validate_order
from .services.xmlGeneraiton import generate_xml
from .utils.helper import to_iso_date

api = Blueprint("main", __name__)

@api.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "running"}), 200

@api.route("v1/buyer/<buyerId>/order", methods=["POST"])
def create_order(buyerId):
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid Json Provided"}), 400
        
    validate_error = validate_order(data, buyerId)
    
    data["order_date"] = to_iso_date(data.get("order_date"))
    data["delivery_date"] = to_iso_date(data.get("delivery_date"))
    
    if validate_error:
        return jsonify({"error": validate_error}), 400
    
    xml_string = generate_xml(data)
    
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
    
    validate_error = validate_order(data)

    if validate_error:
        return jsonify({"error": validate_error}), 400
    
    if data.get("order_date"):
        data["order_date"] = to_iso_date(data.get("order_date"))

    if data.get("delivery_date"):
        data["delivery_date"] = to_iso_date(data.get("delivery_date"))

    result = update_order_service(buyerId, orderId, data)

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
    
    result = delete_order_service(buyerId, orderId)

    if result.get("status") == 404:
        return jsonify(result), 404

    if result.get("status") == 403:
        return jsonify(result), 403

    if result.get("status") == 409:
        return jsonify(result), 409

    if result.get("status") == 500:
        return jsonify(result), 500

    return jsonify(result), 200
