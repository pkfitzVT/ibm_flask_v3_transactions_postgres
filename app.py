# app.py
import os

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401 – ensure models are imported for migrations
from auth.routes import auth_bp
from extensions import db, migrate
from main.api_routes import api_bp
from main.routes import main_bp

# Pytest sets this env var while running tests; skip guard when present
PYTEST_ENV_VAR = "PYTEST_CURRENT_TEST"
# Manual override for migrations/seed
SKIP_GUARD_ENV_VAR = "FLASK_SKIP_GUARD"


def create_app() -> Flask:
    """Flask application factory."""
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # 1) Load configuration
    # ------------------------------------------------------------------
    app.config.from_pyfile("config.py")

    # ------------------------------------------------------------------
    # 1a) If running tests under pytest, override to in-memory SQLite
    #    (applies only when TESTING or during pytest collection)
    # ------------------------------------------------------------------
    if app.config.get("TESTING", False) or os.getenv(PYTEST_ENV_VAR):
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    # ------------------------------------------------------------------
    # 2) Initialise extensions
    # ------------------------------------------------------------------
    db.init_app(app)
    migrate.init_app(app, db)

    # ------------------------------------------------------------------
    # 3) SAFETY GUARD – protect Postgres in dev/prod
    # ------------------------------------------------------------------
    guard_needed = (
        not app.config.get("TESTING", False)
        and not os.getenv(PYTEST_ENV_VAR)
        and not os.getenv(SKIP_GUARD_ENV_VAR)
        and app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("postgresql://")
    )
    if guard_needed:
        with app.app_context():
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            required_tables = {"users", "transactions"}
            missing = required_tables.difference(inspector.get_table_names())
            if missing:
                missing_csv = ", ".join(sorted(missing))
                raise RuntimeError(
                    "Postgres schema missing tables: "
                    f"{missing_csv}. Run `flask db upgrade` before starting the app."
                )

    # ------------------------------------------------------------------
    # 4) Apply CORS
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 5) Register blueprints
    # ------------------------------------------------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
