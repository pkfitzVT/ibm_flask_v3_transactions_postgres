# tests/test_auth.py

from werkzeug.security import generate_password_hash

from extensions import db
from models import User


def seed_demo_user(app):
    """
    Helper to setup a fresh DB with a single demo_user.
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        demo_user = User(
            name="demo_user", password_hash=generate_password_hash("password123")
        )
        db.session.add(demo_user)
        db.session.commit()


def test_api_login_demo_user(client, app):
    """
    Test the JSON API login endpoint ('/api/login').
    Should return 200 for valid credentials.
    """
    seed_demo_user(app)
    resp = client.post(
        "/api/login", json={"email": "demo_user", "password": "password123"}
    )
    assert resp.status_code == 200
    assert resp.get_json() == {"message": "Logged in"}


def test_api_login_invalid_password(client, app):
    """
    Invalid password should return 401 Unauthorized.
    """
    seed_demo_user(app)
    resp = client.post(
        "/api/login", json={"email": "demo_user", "password": "wrongpass"}
    )
    assert resp.status_code == 401


def test_api_register_new_user(client, app):
    """
    Test the JSON API register endpoint ('/api/register').
    Should return 201 Created for a new email.
    """
    # Clean slate
    with app.app_context():
        db.drop_all()
        db.create_all()

    resp = client.post("/api/register", json={"email": "alice", "password": "s3cret"})
    assert resp.status_code == 201
    assert resp.get_json() == {"message": "Registered successfully"}


def test_api_register_duplicate_user(client, app):
    """
    Registering an existing email should return 400 Bad Request.
    """
    seed_demo_user(app)
    resp = client.post(
        "/api/register", json={"email": "demo_user", "password": "password123"}
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()
