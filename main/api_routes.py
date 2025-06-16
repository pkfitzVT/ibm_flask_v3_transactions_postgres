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
from models import Transaction, User

from .stats import abtest
from .stats.regression import compute_regression

# Configure matplotlib backend after imports
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
    if not email or not pwd:
        return jsonify({"error": "Missing email or password"}), 400
    if User.query.filter_by(name=email).first():
        return jsonify({"error": "Email already registered"}), 400
    new_user = User(name=email, password_hash=generate_password_hash(pwd))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Registered successfully"}), 201


@api_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True) or {}
    email = data.get("email")
    pwd = data.get("password")
    if not email or not pwd:
        return jsonify({"error": "Missing email or password"}), 400
    user = User.query.filter_by(name=email).first()
    if not user or not check_password_hash(user.password_hash, pwd):
        return jsonify({"error": "Invalid credentials"}), 401
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


# --- Transactions endpoints ---
@api_bp.route("/transactions", methods=["POST"])
@login_required
def create_transaction():
    data = request.get_json() or {}
    dt_str = data.get("dateTime")
    amt = data.get("amount")

    # 1) Validate presence
    if not dt_str or amt is None:
        return jsonify({"error": "Missing dateTime or amount"}), 400

    # 2) Parse
    try:
        dt_val = datetime.fromisoformat(dt_str)
        amount_val = float(amt)
    except ValueError:
        return jsonify({"error": "Invalid dateTime or amount format"}), 400

    # 3) Persist
    txn = Transaction(
        user_id=session["user_id"],
        date_time=dt_val,
        amount=amount_val,
    )
    db.session.add(txn)
    db.session.commit()

    # 4) Return with amount as a number, not a string
    return (
        jsonify(
            {
                "id": txn.id,
                "dateTime": txn.date_time.isoformat(),
                "amount": float(txn.amount),  # <— here
            }
        ),
        201,
    )


@api_bp.route("/transactions", methods=["GET"])
@login_required
def list_transactions():
    payload = []
    for t in Transaction.query.all():
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


@api_bp.route("/transactions/<int:txn_id>", methods=["PUT", "PATCH"])
@login_required
def update_transaction(txn_id):
    data = request.get_json(force=True) or {}
    txn = Transaction.query.get(txn_id)
    if not txn:
        return jsonify({"error": "Not found"}), 404
    if "dateTime" in data:
        try:
            txn.date_time = datetime.fromisoformat(data["dateTime"])
        except ValueError:
            return jsonify({"error": "Invalid dateTime format"}), 400
    if "amount" in data:
        txn.amount = float(data["amount"])
    db.session.commit()
    return (
        jsonify(
            {
                "id": txn.id,
                "dateTime": txn.date_time.isoformat(),
                "amount": float(txn.amount),
            }
        ),
        200,
    )


@api_bp.route("/transactions/<int:txn_id>", methods=["DELETE"])
@login_required
def delete_transaction(txn_id):
    txn = Transaction.query.get(txn_id)
    if not txn:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(txn)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200


# --- Analysis endpoints ---


@api_bp.route("/analysis/abtest", methods=["GET", "POST"])
@login_required
def api_ab_test():
    """
    A/B test endpoint:
      - GET returns default A/B test results
      - POST accepts JSON { group_by, param_a, param_b } for custom test
    Response JSON: {
      "groupA": [...],
      "groupB": [...],
      "p_value": float or None,
      "boxplot_img": base64-string
    }
    """
    try:
        # 1) Fetch this user's transactions from the database
        user_id = session.get("user_id")
        txns = Transaction.query.filter_by(user_id=user_id).all()

        # 2) Build the flat dicts that run_ab_test() expects
        records = [
            {
                "dateTime": t.date_time.isoformat(),
                # include any grouping field your tests expect:
                "description": t.description,
                "amount": float(t.amount),
            }
            for t in txns
        ]

        # 3) Monkey-patch the A/B-test module so run_ab_test() sees YOUR data
        abtest.transactions = records

        # 4) Call run_ab_test() (GET uses defaults; POST can override via JSON)
        if request.method == "POST":
            params = request.get_json(force=True) or {}
            result = abtest.run_ab_test(
                group_by=params.get("group_by"),
                param_a=params.get("param_a"),
                param_b=params.get("param_b"),
            )
        else:
            result = abtest.run_ab_test()

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.exception("Error running A/B test")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/analysis/regression", methods=["GET"])
@login_required
def api_regression():
    """
    Regression endpoint:
      - GET returns slope, intercept, r_squared, chart_img
      - Operates over all transactions (no user_id filter)
    """
    # 1) Time-of-day filter
    period = request.args.get("period", "all").lower()
    if period == "morning":
        hours = range(0, 12)
    elif period == "noon":
        hours = (12,)
    elif period == "afternoon":
        hours = range(13, 18)
    else:
        hours = None

    # 2) Date-range filters
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")
    try:
        start_dt = datetime.fromisoformat(start_str) if start_str else None
        end_dt = datetime.fromisoformat(end_str) if end_str else None
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    # 3) Fetch all transactions (no user filter)
    txns = Transaction.query.all()

    # 4) Build (datetime, amount) pairs and apply filters
    pairs = []
    for t in txns:
        dt = t.date_time
        if (start_dt and dt < start_dt) or (end_dt and dt > end_dt):
            continue
        if hours and dt.hour not in hours:
            continue
        pairs.append((dt, float(t.amount)))

    # 5) If no data, return nulls
    if not pairs:
        return (
            jsonify(
                {
                    "slope": None,
                    "intercept": None,
                    "r_squared": None,
                    "chart_img": None,
                }
            ),
            200,
        )

    # 6) Compute regression
    ts_amounts = [(d.timestamp(), a) for d, a in pairs]
    stats = compute_regression(ts_amounts)
    slope = float(stats["slope"])
    intercept = float(stats["intercept"])
    r_squared = float(stats["r_squared"])

    # 7) Render chart
    matplotlib.use("Agg")
    fig, ax = plt.subplots(figsize=(8, 4))
    dates = [d for d, _ in pairs]
    amounts = [a for _, a in pairs]
    ax.scatter(dates, amounts, alpha=0.6, label="Data")
    xs = np.array([d.timestamp() for d in dates])
    ax.plot(dates, intercept + slope * xs, linewidth=2, label="Trend")

    locator = mdates.AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    fig.autofmt_xdate()
    ax.set_title("Regression Analysis")
    ax.set_ylabel("Amount")
    ax.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    chart_b64 = base64.b64encode(buf.read()).decode("ascii")

    # 8) Return JSON
    return (
        jsonify(
            {
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_squared,
                "chart_img": chart_b64,
            }
        ),
        200,
    )
