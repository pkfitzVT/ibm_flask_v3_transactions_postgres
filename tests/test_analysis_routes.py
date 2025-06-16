# tests/test_analysis_routes.py
# flake8: noqa: E402
from datetime import datetime, timedelta

import pytest
from werkzeug.security import generate_password_hash

from extensions import db
from models import Transaction, User


def seed_user_and_transactions(app):
    """
    Seed a demo user and a set of transactions for analysis tests.
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        # create demo user
        demo = User(name="demo_user", password_hash=generate_password_hash("pass123"))
        db.session.add(demo)
        db.session.commit()
        # seed transactions across two groups for A/B test
        for i in range(5):
            t = Transaction(
                user_id=demo.id,
                date_time=datetime(2025, 6, 1) + timedelta(days=i),
                amount=100 + i,
                description=f"txn {i}",
            )
            db.session.add(t)
        db.session.commit()


def login(client):
    resp = client.post("/api/login", json={"email": "demo_user", "password": "pass123"})
    assert resp.status_code == 200
    return resp


def test_api_get_abtest_defaults(client, app):
    """
    GET /api/analysis/abtest returns default A/B results with p_value, groupA, groupB
    """
    seed_user_and_transactions(app)
    login(client)
    resp = client.get("/api/analysis/abtest")
    assert resp.status_code == 200
    data = resp.get_json()
    # assert keys exist and correct types (p_value may be None)
    assert "p_value" in data and (
        data["p_value"] is None or isinstance(data["p_value"], float)
    )
    assert "groupA" in data and isinstance(data["groupA"], list)
    assert "groupB" in data and isinstance(data["groupB"], list)


def test_api_post_abtest_with_params(client, app):
    """
    POST /api/analysis/abtest with custom params returns valid result
    """
    seed_user_and_transactions(app)
    login(client)
    payload = {"group_by": "date_time", "param_a": "amount", "param_b": "amount"}
    resp = client.post("/api/analysis/abtest", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "p_value" in data
    assert "groupA" in data and isinstance(data["groupA"], list)
    assert "groupB" in data and isinstance(data["groupB"], list)


def test_api_get_regression_default(client, app):
    """
    GET /api/analysis/regression returns slope, intercept, r_squared, chart_img
    """
    seed_user_and_transactions(app)
    login(client)
    resp = client.get("/api/analysis/regression")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "slope" in data and (
        data["slope"] is None or isinstance(data["slope"], float)
    )
    assert "intercept" in data and (
        data["intercept"] is None or isinstance(data["intercept"], float)
    )
    assert "r_squared" in data and (
        data["r_squared"] is None or isinstance(data["r_squared"], float)
    )
    assert "chart_img" in data and (
        data["chart_img"] is None or isinstance(data["chart_img"], str)
    )
