# main/api_routes.py

import base64
import io
from datetime import datetime

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from flask import Blueprint, current_app, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

from auth.routes import users
from auth.utils import login_required
from extensions import db
from models import User

from .data import transactions
from .stats.abtest import run_ab_test
from .stats.regression import compute_regression  # import your stat function

# Move the Agg backend setup *after* all imports
matplotlib.use("Agg")


api_bp = Blueprint("api", __name__, url_prefix="/api")
CORS(
    api_bp,
    supports_credentials=True,
    origins="http://localhost:3000",
    methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
)

# --- Auth endpoints ---


@api_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True) or {}
    email = data.get("email")
    pwd = data.get("password")

    # 1) Validate inputs
    if not email or not pwd:
        return jsonify({"error": "Missing email or password"}), 400

    # 2) Check for existing user in the DB
    if User.query.filter_by(name=email).first():
        return jsonify({"error": "Email already registered"}), 400

    # 3) Create and persist the new user
    new_user = User(name=email, password_hash=generate_password_hash(pwd))
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Registered successfully"}), 201


@api_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True) or {}
    email = data.get("email")
    pwd = data.get("password")

    # 1) Validate presence
    if not email or not pwd:
        return jsonify({"error": "Missing email or password"}), 400

    # 2) Look up the user in Postgres
    user = User.query.filter_by(name=email).first()
    if not user or not check_password_hash(user.password_hash, pwd):
        return jsonify({"error": "Invalid credentials"}), 401

    # 3) Success — store session and return
    session["user_id"] = user.id
    return jsonify({"message": "Logged in"}), 200


@api_bp.route("/logout", methods=["POST"])
@login_required
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@api_bp.route("/me", methods=["GET"])
def api_me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"id": user["id"], "email": user["email"]}), 200


# --- Transactions endpoints with full datetime support and unique IDs ---


@api_bp.route("/transactions", methods=["GET"])
@login_required
def list_transactions():
    payload = []
    for t in transactions:
        copy_t = t.copy()
        if "dateTime" not in copy_t:
            original = copy_t.get("date")
            if isinstance(original, datetime):
                copy_t["dateTime"] = original.isoformat()
            elif original:
                copy_t["dateTime"] = f"{original}T00:00:00"
            else:
                copy_t["dateTime"] = None
        payload.append(copy_t)
    return jsonify(payload), 200


@api_bp.route("/transactions", methods=["POST"])
@login_required
def create_transaction():
    try:
        data = request.get_json() or {}
        dt = data.get("dateTime")
        amt = data.get("amount")
        if not dt or amt is None:
            return jsonify({"error": "Missing dateTime or amount"}), 400
        max_id = max((t["id"] for t in transactions), default=0)
        new_txn = {"id": max_id + 1, "dateTime": dt, "amount": amt}
        transactions.append(new_txn)
        return jsonify(new_txn), 201
    except Exception:
        current_app.logger.exception("Error creating transaction")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/transactions/<int:txn_id>", methods=["PUT", "PATCH"])
@login_required
def update_transaction(txn_id):
    try:
        data = request.get_json() or {}
        txn = next((t for t in transactions if t["id"] == txn_id), None)
        if not txn:
            return jsonify({"error": "Not found"}), 404
        if "dateTime" in data:
            txn["dateTime"] = data["dateTime"]
        if "amount" in data:
            txn["amount"] = data["amount"]
        return jsonify(txn), 200
    except Exception:
        current_app.logger.exception("Error updating transaction")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/transactions/<int:txn_id>", methods=["DELETE"])
@login_required
def delete_transaction(txn_id):
    global transactions
    transactions = [t for t in transactions if t["id"] != txn_id]
    return jsonify({"message": "Deleted"}), 200


# --- New Analysis endpoints (JSON only) ---


@api_bp.route("/analysis/abtest", methods=["GET", "POST"])
@login_required
def api_ab_test():
    try:
        if request.method == "POST":
            data = request.get_json(force=True) or {}
            group_by = data.get("group_by")
            param_a = data.get("param_a")
            param_b = data.get("param_b")
            if not group_by or not param_a or not param_b:
                return jsonify({"error": "Missing parameters"}), 400
            result = run_ab_test(group_by, param_a, param_b)
        else:
            result = run_ab_test()
        return jsonify(result), 200
    except Exception as e:
        current_app.logger.exception("Error running A/B test")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/analysis/regression", methods=["GET"])
@login_required
def api_regression():
    period = request.args.get("period", "all").lower()
    hours = (
        list(range(0, 12))
        if period == "morning"
        else [12]
        if period == "noon"
        else list(range(13, 18))
        if period == "afternoon"
        else None
    )

    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    start_dt = datetime.fromisoformat(start_str) if start_str else None
    end_dt = datetime.fromisoformat(end_str) if end_str else None

    pairs = []
    for t in transactions:
        raw = t.get("dateTime") or t.get("date")
        if not raw:
            continue
        if isinstance(raw, datetime):
            dt = raw
        else:
            s = raw if "T" in raw else f"{raw}T00:00:00"
            try:
                dt = datetime.fromisoformat(s)
            except ValueError:
                continue

        if start_dt and dt < start_dt:
            continue
        if end_dt and dt > end_dt:
            continue
        if hours and dt.hour not in hours:
            continue

        pairs.append((dt, float(t["amount"])))

    if not pairs:
        return (
            jsonify(
                {"slope": None, "intercept": None, "r_squared": None, "chart_img": None}
            ),
            200,
        )

    ts_amounts = [(dt.timestamp(), amt) for dt, amt in pairs]
    stats = compute_regression(ts_amounts)
    slope = stats["slope"]
    intercept = stats["intercept"]
    r2 = stats["r_squared"]

    fig, ax = plt.subplots(figsize=(8, 4))
    dates = [dt for dt, _ in pairs]
    amounts = [amt for _, amt in pairs]
    ax.scatter(dates, amounts, alpha=0.6, label="Data")

    xs_ts = np.array([d.timestamp() for d in dates])
    y_pred = intercept + slope * xs_ts
    ax.plot(dates, y_pred, linewidth=2, label="Trend")

    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()

    ax.set_title("Regression Analysis")
    ax.set_ylabel("Amount")
    ax.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    chart_b64 = base64.b64encode(buf.read()).decode("ascii")

    return (
        jsonify(
            {
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r2),
                "chart_img": chart_b64,
            }
        ),
        200,
    )
