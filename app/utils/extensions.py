from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def get_api_key_identifier():
    from flask import request
    try:
        return request.headers.get("api-key") or get_remote_address()
    except RuntimeError:
        return get_remote_address()

limiter = Limiter(
    key_func=get_api_key_identifier,
    default_limits=["1000 per day", "200 per hour"],
    storage_uri="memory://"
)