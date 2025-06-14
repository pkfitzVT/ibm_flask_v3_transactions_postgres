# flake8: noqa: E402, F401
import os
import sys

import pytest
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

# Ensure project root is on the import path
top = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if top not in sys.path:
    sys.path.insert(0, top)

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
        # Reset database state on each test session
        db.drop_all()
        db.create_all()
        # Seed a demo user for authentication
        demo_user = User(
            name="demo_user", password_hash=generate_password_hash("password123")
        )
        db.session.add(demo_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    yield app
    # Teardown: drop all tables after tests complete
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
