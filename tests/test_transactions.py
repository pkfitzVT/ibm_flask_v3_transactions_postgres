# tests/test_transactions.py

from datetime import datetime

from werkzeug.security import generate_password_hash

from extensions import db
from models import Transaction, User


def seed_demo_user_txn(app):
    """Helper to seed a demo user and a single transaction for testing."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(
            name="demo_user", password_hash=generate_password_hash("password123")
        )
        db.session.add(user)
        db.session.commit()
        txn = Transaction(
            user_id=user.id,
            date_time=datetime.fromisoformat("2025-06-01T00:00:00"),
            amount=100.0,
        )
        db.session.add(txn)
        db.session.commit()
        return user.id, txn.id


def test_api_update_transaction(client, app):
    """
    Update an existing transaction via PUT and verify the new values.
    """
    user_id, txn_id = seed_demo_user_txn(app)

    # Perform login
    resp_login = client.post(
        "/api/login", json={"email": "demo_user", "password": "password123"}
    )
    assert resp_login.status_code == 200

    # Act: update the transaction
    new_data = {"dateTime": "2025-06-10T12:30:00", "amount": 150.0}
    resp = client.put(f"/api/transactions/{txn_id}", json=new_data)

    # Assert: correct status and payload
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("dateTime") == new_data["dateTime"]
    assert data.get("amount") == new_data["amount"]


def test_api_update_nonexistent_transaction(client, app):
    """
    Attempt to update a non-existent transaction and expect a 404.
    """
    # Seed only the user
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(
            name="demo_user", password_hash=generate_password_hash("password123")
        )
        db.session.add(user)
        db.session.commit()

    # Perform login
    resp_login = client.post(
        "/api/login", json={"email": "demo_user", "password": "password123"}
    )
    assert resp_login.status_code == 200

    # Act: try to update a missing transaction
    resp = client.put("/api/transactions/9999", json={"amount": 200})
    assert resp.status_code == 404
    assert "error" in resp.get_json()
