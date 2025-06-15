# app.py
import os

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401
from auth.routes import auth_bp
from extensions import db, migrate
from main.api_routes import api_bp
from main.routes import main_bp

# Pytest sets this env var while running tests; we use it to skip the guard
PYTEST_ENV_VAR = "PYTEST_CURRENT_TEST"


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)

    # 1) config
    app.config.from_pyfile("config.py")

    # 2) init extensions so db.engine exists
    db.init_app(app)
    migrate.init_app(app, db)

    # 3) SAFETY GUARD – block destructive ops on Postgres outside tests
    guard_needed = (
        not app.config.get("TESTING", False)
        and not os.getenv(PYTEST_ENV_VAR)
        and app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql://")
    )
    if guard_needed:
        with app.app_context():
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            required = {"users", "transactions"}
            missing = required.difference(inspector.get_table_names())
            if missing:
                missing_csv = ", ".join(sorted(missing))
                raise RuntimeError(
                    "Postgres schema missing tables: "
                    f"{missing_csv}. Run `flask db upgrade`."
                )

    # 4) CORS
    CORS(
        app,
        supports_credentials=True,
        resources={
            r"/api/*": {
                "origins": "http://localhost:3000",
                "methods": [
                    "GET",
                    "POST",
                    "PUT",
                    "PATCH",
                    "DELETE",
                    "OPTIONS",
                ],
            }
        },
    )

    # 5) blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
