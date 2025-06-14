# tests/test_regression.py

import pytest

from app import create_app
from main.stats.regression import compute_regression


@pytest.fixture
def client():
    # 1) Build a fresh Flask app with testing config
    app = create_app()
    app.config["TESTING"] = True
    # 2) Use the Flask test client
    with app.test_client() as client:
        yield client


def test_regression_page_requires_login(client):
    resp = client.get("/analysis/regression")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_regression_perfect_line():
    """
    A perfect y = 2x + 1 line over 3 points should yield:
      slope ≈ 2.0, intercept ≈ 1.0, r2 ≈ 1.0
    """
    data = [(0, 1), (1, 3), (2, 5)]  # y = 2x + 1
    result = compute_regression(data)
    assert pytest.approx(result["slope"], rel=1e-3) == 2.0
    assert pytest.approx(result["intercept"], rel=1e-3) == 1.0
    assert pytest.approx(result["r2"], rel=1e-3) == 1.0


def test_regression_constant_line():
    """
    A constant line y = 4 should yield slope ≈ 0.0, intercept ≈ 4.0.
    R² may be undefined or 0 (implementation-dependent), but slope/intercept matter.
    """
    data = [(0, 4), (1, 4), (2, 4)]
    result = compute_regression(data)
    assert pytest.approx(result["slope"], rel=1e-3) == 0.0
    assert pytest.approx(result["intercept"], rel=1e-3) == 4.0
