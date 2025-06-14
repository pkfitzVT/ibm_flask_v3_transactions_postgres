# app.py
# flake8: noqa: E402
from flask import Flask
from flask_cors import CORS

# 1) import your extensions
from extensions import db, migrate


def create_app():
    app = Flask(__name__)

    # 2) load config (SECRET_KEY, SQLALCHEMY_DATABASE_URI via .env/config.py)
    app.config.from_pyfile("config.py")

    # 3) initialize your extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # 4) apply CORS as before
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

    # 5) import models so Flask-Migrate knows about them
    #    (you can also do this in extensions or a top-level __init__.py)
    import models  # noqa: F401

    # 6) register your blueprints
    from auth.routes import auth_bp
    from main.api_routes import api_bp
    from main.routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)  # mounts at /add, /edit, /transactions, etc.
    app.register_blueprint(api_bp)  # mounts at /api/*

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
