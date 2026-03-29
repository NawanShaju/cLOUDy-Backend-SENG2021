from flask import Blueprint, jsonify, request, Response
from app.services.order_service import create_order_v2_service
from app.utils.xml_generation import generate_xml_v2
from .services.validate_order import validate_order
from .services.api_key import validate_api_key
from .services.db_services.xml_db import xml_to_db
from .utils.helper import is_valid_uuid, to_iso_date
from database.PostgresDB import PostgresDB
from app.utils.extensions import limiter

api = Blueprint("v2", __name__)

@api.route("/v2/buyer/<buyerId>/order", methods=["POST"])
@validate_api_key
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

    validate_error = validate_order(data, buyerId)
    if validate_error:
        return jsonify({"error": validate_error}), 400

    with PostgresDB() as db:
        result = create_order_v2_service(db, data, buyerId)

        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]

        order_id = result["order_id"]
        buyer_data = result["buyer_data"]

        xml_string = generate_xml_v2(data, order_id, buyerId, buyer_data)
        xml_to_db(db, xml_string, order_id)

    return Response(
        xml_string,
        mimetype='application/xml',
        status=200
    )
    