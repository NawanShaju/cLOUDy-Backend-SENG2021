import requests
from flask import Blueprint, jsonify, request, Response
from app.services.api_key import validate_api_key
 
proxy = Blueprint("proxy", __name__)

@proxy.route("/proxy", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@validate_api_key
def forward_request():
    target_url = request.args.get("url")
    if not target_url:
        return jsonify({"error": "Missing required query parameter: url"}), 400
 
    forward_params = {k: v for k, v in request.args.items() if k != "url"}
 
    excluded_headers = {
        "host", "content-length", "transfer-encoding",
        "connection", "keep-alive", "proxy-authenticate",
        "proxy-authorization", "te", "trailers", "upgrade",
    }
    forward_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in excluded_headers
    }
 
    body = request.get_data()
 
    try:
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=forward_headers,
            params=forward_params,
            data=body,
            timeout=30,
            allow_redirects=True,
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Could not connect to {target_url}"}), 502
    except requests.exceptions.Timeout:
        return jsonify({"error": f"Request to {target_url} timed out"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 502
 
    excluded_response_headers = {
        "content-encoding", "transfer-encoding", "connection",
        "keep-alive", "proxy-authenticate", "proxy-authorization",
        "te", "trailers", "upgrade",
    }
    response_headers = {
        k: v for k, v in response.headers.items()
        if k.lower() not in excluded_response_headers
    }
 
    return Response(
        response.content,
        status=response.status_code,
        headers=response_headers,
    )