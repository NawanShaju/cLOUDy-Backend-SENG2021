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