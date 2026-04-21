from flask import Flask
from .utils.extensions import limiter
from .routes import api, swaggerui_blueprint, register_swagger_yaml
from .proxy_route import proxy
from .routes_v2 import api as api_v2
from flask_cors import CORS
import app.config.run

def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    limiter.init_app(app)
    
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(api_v2, url_prefix="/api")
    app.register_blueprint(proxy, url_prefix="/api")
    register_swagger_yaml(app)
    app.register_blueprint(swaggerui_blueprint)
    return app