from flask import Flask
from .utils.extensions import limiter
from .routes import api, swaggerui_blueprint, register_swagger_yaml
from .proxy_route import proxy
from .routes_v2 import api as api_v2
from flask_cors import CORS
from database.PostgresDB import PostgresDB

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

    with PostgresDB() as db:
        db.execute_insert_update_delete("""
            CREATE TABLE IF NOT EXISTS inventory (
                seller_id UUID NOT NULL,
                inventory_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                item_name VARCHAR(255) NOT NULL,
                item_description TEXT,
                purchase_price NUMERIC(12,2) NOT NULL CHECK (purchase_price >= 0),
                quantity INTEGER NOT NULL CHECK (quantity >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_inventory_seller
                    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id) ON DELETE CASCADE,
                CONSTRAINT unique_inventory_item_per_seller UNIQUE (seller_id, item_name)
            )
        """, {})

    return app