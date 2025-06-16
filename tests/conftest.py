# tests/conftest.py
# flake8: noqa: E402  # Allow imports before code for environment setup
import os
import sys

# Skip Postgres safety guard during tests
os.environ["FLASK_SKIP_GUARD"] = "1"

# Add project root to import path so extensions and models can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import User

# Testing configuration: in-memory SQLite for fast, isolated tests
test_config = {
    "TESTING": True,
    "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "SECRET_KEY": "test-secret",
}


@pytest.fixture(scope="session")
def app():
    """
    Create and configure a new Flask app instance for testing.
    """
    app = create_app()
    app.config.update(test_config)
    with app.app_context():
        db.drop_all()
        db.create_all()
        demo_user = User(
            name="demo_user", password_hash=generate_password_hash("password123")
        )
        db.session.add(demo_user)
        db.session.commit()
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """
    Provides a Flask test client for each test function.
    """
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """
    Provides a Click runner for Flask CLI commands.
    """
    return app.test_cli_runner()
