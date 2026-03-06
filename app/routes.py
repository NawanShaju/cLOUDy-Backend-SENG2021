from flask import Blueprint, jsonify, request
from services.orders import delete_order

main_bp = Blueprint("main", __name__)

@main_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200



@main_bp.route("/api/v1/buyer/<buyerId>/order/<orderId>", methods=["DELETE"])
def delete_order_route(buyerId, orderId):

    result = delete_order(buyerId, orderId)

    if result.get("status") == 404:
        return jsonify(result), 404

    if result.get("status") == 409:
        return jsonify(result), 409

    if result.get("status") == 500:
        return jsonify(result), 500

    return jsonify(result), 200




# @main_bp.route("/api/v1/buyer/<buyer_id>/order/<order_id>", methods=["DELETE"])
# def delete_order(buyer_id, order_id):
#     # authentication check (401)
#     ...
#     # forbidden check (403)
#     ...

#     order = orders_db[buyer_id][order_id]
#     # check order status (409)
#     ...
#     #delete order
#     order["status"] = "CANCELLED"
#     return jsonify({
#         "orderId": order_id,
#         "status":  "CANCELLED",
#         "message": "Order deleted succesfully"
#     }), 200