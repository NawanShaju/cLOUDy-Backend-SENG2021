from flask import Flask
from .routes import main_bp

def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    app.register_blueprint(main_bp, url_prefix="/api")

    return app