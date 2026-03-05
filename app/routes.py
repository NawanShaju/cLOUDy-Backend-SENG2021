from flask import Blueprint, jsonify, request

main_bp = Blueprint("main", __name__)

@main_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200
