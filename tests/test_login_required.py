# tests/test_login_required.py

import pytest

from app import create_app


@pytest.fixture
def client():
    # 1) Build a fresh Flask app with testing config
    app = create_app()
    app.config["TESTING"] = True
    # 2) Use the Flask test client
    with app.test_client() as client:
        yield client


def test_transactions_requires_login(client):
    """
    If you hit /transactions without logging in,
    you should be redirected to the login page.
    """
    resp = client.get("/transactions")
    # 302 = redirect
    assert resp.status_code == 302
    # ensure it’s pointing to /login (or your login route)
    assert "/login" in resp.headers["Location"]
