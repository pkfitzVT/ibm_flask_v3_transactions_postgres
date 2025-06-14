# app.py

from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    app.config.from_pyfile("config.py")  # e.g. SECRET_KEY

    # Allow all the HTTP methods your API uses, including preflight OPTIONS and PATCH
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

    # import & register blueprints
    from auth.routes import auth_bp
    from main.api_routes import api_bp
    from main.routes import main_bp

    app.register_blueprint(auth_bp)  # mounts at /
    app.register_blueprint(
        main_bp, url_prefix=""
    )  # mounts at /add, /edit, /transactions, etc.
    app.register_blueprint(api_bp)  # mounts at /api/*

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
