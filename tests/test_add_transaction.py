# tests/test_add_transaction.py

import pytest

from app import create_app
from main.data import transactions  # <— import your in-memory store


@pytest.fixture
def client():
    # 1) Build a fresh Flask app in TESTING mode
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_add_requires_login(client):
    """GET /add must redirect if not logged in."""
    resp = client.get("/add")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_add_transaction(client):
    """POST /add with valid data should append a transaction."""
    # Log in first (adjust if you have a register helper)
    client.post("/register", data={"email": "a@b.com", "password": "pw"})
    client.post("/login", data={"email": "a@b.com", "password": "pw"})

    # Start from a clean slate
    transactions.clear()
    assert len(transactions) == 0

    # Exercise the feature
    resp = client.post(
        "/add", data={"date": "2025-06-10", "amount": "123.45"}, follow_redirects=True
    )
    page = resp.get_data(as_text=True)

    # These will fail until /add is implemented correctly
    assert "123.45" in page
    assert len(transactions) == 1
    assert transactions[0]["amount"] == 123.45
