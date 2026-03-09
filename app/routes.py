from flask import Blueprint, jsonify, request, Response
from .services.validate_order import validate_order
from .services.xmlGeneraiton import generate_xml
from .services.orderdb import create_order_db
from .services.xmldb import xml_to_db
from .utils.helper import to_iso_date
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