# flake8: noqa
from datetime import datetime

import pytest
from werkzeug.security import generate_password_hash

from extensions import db
from models import Transaction, User


def seed_demo_user_txns(app):
    """Helper to setup a fresh DB with a single demo_user and seed transactions."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        # create demo user
        demo = User(
            name="demo_user", password_hash=generate_password_hash("password123")
        )
        db.session.add(demo)
        db.session.commit()
        # seed a couple of transactions
        tx1 = Transaction(
            user_id=demo.id,
            date_time=datetime(2025, 1, 1, 9, 0),
            amount=100.0,
            description="Test txn 1",
        )
        tx2 = Transaction(
            user_id=demo.id,
            date_time=datetime(2025, 1, 2, 12, 0),
            amount=200.0,
            description="Test txn 2",
        )
        db.session.add_all([tx1, tx2])
        db.session.commit()


def test_list_transactions_fails_with_in_memory(client, app):
    """
    Before wiring to the DB, the in-memory list should not include our seeded transactions.
    """
    seed_demo_user_txns(app)
    # login
    client.post("/api/login", json={"email": "demo_user", "password": "password123"})
    # list
    resp = client.get("/api/transactions")
    data = resp.get_json()
    # Expect not to see our DB transactions until route is updated
    assert all(tx["id"] not in (1, 2) for tx in data)


def test_list_transactions_db_backed(client, app):
    """
    After wiring the route to SQLAlchemy, GET /api/transactions should return our seeded rows.
    """
    seed_demo_user_txns(app)
    # login
    client.post("/api/login", json={"email": "demo_user", "password": "password123"})
    # list
    resp = client.get("/api/transactions")
    data = resp.get_json()
    ids = {tx["id"] for tx in data}
    assert {1, 2}.issubset(ids)
