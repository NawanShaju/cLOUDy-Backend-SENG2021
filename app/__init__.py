from flask import Flask
from .routes import api

def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    app.register_blueprint(api, url_prefix="/api")

    return app