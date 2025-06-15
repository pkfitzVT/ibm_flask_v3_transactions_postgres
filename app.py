# app.py

from flask import Flask
from flask_cors import CORS

# 2) import models so Flask-Migrate knows about them
#    (we suppress only the 'unused import' warning here)
import models  # noqa: F401

# 3) import blueprints
from auth.routes import auth_bp

# 1) import your extensions
from extensions import db, migrate
from main.api_routes import api_bp
from main.routes import main_bp


def create_app():
    app = Flask(__name__)

    # 4) load config (SECRET_KEY, SQLALCHEMY_DATABASE_URI via .env/config.py)
    app.config.from_pyfile("config.py")

    # 5) initialize your extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # 6) apply CORS
    CORS(
        app,
        supports_credentials=True,
        resources={
            r"/api/*": {
                "origins": "http://localhost:3000",
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            }
        },
    )

    # 7) register your blueprints
    app.register_blueprint(auth_bp)  # mounts /auth routes
    app.register_blueprint(main_bp)  # mounts /, /add, /edit, /transactions
    app.register_blueprint(api_bp)  # mounts /api/*

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
