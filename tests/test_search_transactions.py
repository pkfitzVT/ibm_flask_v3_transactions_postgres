import pytest

from app import create_app
from main.data import transactions


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_search_requires_login(client):
    """GET /search must redirect if not authenticated."""
    resp = client.get("/search")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_search_filters_transactions(client):
    """POST /search returns only transactions within the given range."""
    # 1) Log in
    client.post("/register", data={"email": "a@b.com", "password": "pw"})
    client.post("/login", data={"email": "a@b.com", "password": "pw"})

    # 2) Seed some transactions
    transactions.clear()
    transactions.extend(
        [
            {"id": 1, "date": "2025-01-01", "amount": 50.00},
            {"id": 2, "date": "2025-01-02", "amount": 100.00},
            {"id": 3, "date": "2025-01-03", "amount": 150.00},
        ]
    )

    # 3) Search for amounts between 60 and 140
    resp = client.post(
        "/search", data={"min_amount": "60", "max_amount": "140"}, follow_redirects=True
    )
    page = resp.get_data(as_text=True)

    # 4) Assert only the middle transaction shows up
    assert "100.00" in page
    assert "50.00" not in page
    assert "150.00" not in page
