import requests
from flask import Blueprint, jsonify, request, Response
from app.services.api_key import validate_api_key

proxy = Blueprint("proxy", __name__)

@proxy.route("/v1/proxy", methods=["POST"])
def proxy_request():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Request body is required"}), 400

    url = body.get("url")
    if not url:
        return jsonify({"error": "url is required"}), 400

    method = body.get("method", "GET").upper()
    headers = body.get("headers", {})
    params = body.get("params", {})
    data = body.get("body")

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=15,
        )
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type", "application/json"),
        )

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request to external API timed out"}), 504

    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to {url}"}), 502

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    