import pytest  # noqa: F401  # explicitly tell linter this import is neededv

from app import create_app
from main.stats.abtest import remove_outliers, t_test


@pytest.fixture
def client():
    # 1) Build a fresh Flask app with testing config
    app = create_app()
    app.config["TESTING"] = True
    # 2) Use the Flask test client
    with app.test_client() as client:
        yield client


def test_remove_outliers():
    data = [1, 2, 2, 100, 3, 2]
    cleaned = remove_outliers(data)
    assert 100 not in cleaned
    assert all(1 <= x <= 3 for x in cleaned)


def test_t_test_returns_pvalue_between_0_and_1():
    groupA = [10, 12, 11, 13]
    groupB = [20, 22, 21, 23]
    p = t_test(groupA, groupB)
    assert 0.0 <= p <= 1.0


def test_abtest_requires_login(client):
    """GET /analysis/abtest must redirect to login."""
    resp = client.get("/analysis/abtest")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
