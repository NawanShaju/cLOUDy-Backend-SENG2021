from flask import Flask
from .utils.extensions import limiter
from .routes import api, swaggerui_blueprint, register_swagger_yaml

def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    limiter.init_app(app)
    
    app.register_blueprint(api, url_prefix="/api")
    register_swagger_yaml(app)
    app.register_blueprint(swaggerui_blueprint)
    return app