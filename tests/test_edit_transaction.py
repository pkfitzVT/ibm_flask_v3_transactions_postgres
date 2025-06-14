import pytest

from app import create_app
from main.data import transactions


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_edit_requires_login(client):
    """Unauthenticated GET /edit/1 must redirect to login."""
    resp = client.get("/edit/1")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_edit_changes_transaction(client):
    """POST /edit/1 updates the in-memory transaction correctly."""
    # 1) Log in
    client.post("/register", data={"email": "u@u.com", "password": "pw"})
    client.post("/login", data={"email": "u@u.com", "password": "pw"})

    # 2) Seed a single transaction
    transactions.clear()
    transactions.append({"id": 1, "date": "2025-06-10", "amount": 100.00})
    assert transactions[0]["amount"] == 100.00

    # 3) Edit it
    client.post(
        "/edit/1",
        data={"date": "2025-06-11", "amount": "150.00"},
        follow_redirects=False,
    )

    # 4) Verify the data object changed
    assert transactions[0]["date"] == "2025-06-11"
    assert transactions[0]["amount"] == 150.00


def test_edit_displays_updated_values(client):
    """After edit, GET /transactions page shows the new date
    and amount (two decimals)."""
    # 1) Log in
    client.post("/register", data={"email": "u@u.com", "password": "pw"})
    client.post("/login", data={"email": "u@u.com", "password": "pw"})

    # 2) Seed a single transaction and perform edit
    transactions.clear()
    transactions.append({"id": 1, "date": "2025-06-10", "amount": 100.00})
    client.post(
        "/edit/1",
        data={"date": "2025-06-11", "amount": "150.00"},
        follow_redirects=True,
    )

    # 3) Request the transactions list
    resp = client.get("/transactions")
    assert resp.status_code == 200
    page = resp.get_data(as_text=True)

    # 4) Assert updated date and formatted amount appear in page
    assert "2025-06-11" in page
    assert "150.00" in page
