# main/api_routes.py

import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app, session
from auth.utils import login_required
from .data import transactions
from auth.routes import users
from .stats.regression import compute_regression  # import your stat function
from .stats.abtest import run_ab_test
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


api_bp = Blueprint('api', __name__, url_prefix='/api')
CORS(
    api_bp,
    supports_credentials=True,
    origins="http://localhost:3000",
    methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"]
)

# --- Auth endpoints ---

@api_bp.route('/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json(force=True) or {}
        current_app.logger.debug(f"Register payload: {data!r}")

        email = data.get('email')
        pwd   = data.get('password')
        if not email or not pwd:
            return jsonify({'error': 'Missing email or password'}), 400

        if any(u['email'] == email for u in users):
            return jsonify({'error': 'Email already registered'}), 400

        pw_hash   = generate_password_hash(pwd)
        new_user  = {'id': len(users) + 1, 'email': email, 'pw_hash': pw_hash}
        users.append(new_user)

        return jsonify({'message': 'Registered successfully'}), 201

    except Exception as e:
        current_app.logger.exception("Registration failed")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email')
    pwd   = data.get('password')
    user = next((u for u in users if u['email'] == email), None)
    if not user or not check_password_hash(user['pw_hash'], pwd):
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = user['id']
    return jsonify({'message': 'Logged in'}), 200

@api_bp.route('/logout', methods=['POST'])
@login_required
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200

@api_bp.route('/me', methods=['GET'])
def api_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': user['id'], 'email': user['email']}), 200


# --- Transactions endpoints with full datetime support and unique IDs ---

@api_bp.route('/transactions', methods=['GET'])
@login_required
def list_transactions():
    # Normalize legacy 'date' field into 'dateTime'
    for t in transactions:
        if 'dateTime' not in t:
            if 'date' in t:
                t['dateTime'] = f"{t.pop('date')}T00:00"
            else:
                t['dateTime'] = None
    return jsonify(transactions), 200

@api_bp.route('/transactions', methods=['POST'])
@login_required
def create_transaction():
    try:
        data = request.get_json() or {}
        dt  = data.get('dateTime')
        amt = data.get('amount')
        if not dt or amt is None:
            return jsonify({'error': 'Missing dateTime or amount'}), 400
        max_id = max((t['id'] for t in transactions), default=0)
        new_txn = {'id': max_id + 1, 'dateTime': dt, 'amount': amt}
        transactions.append(new_txn)
        return jsonify(new_txn), 201
    except Exception:
        current_app.logger.exception('Error creating transaction')
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/transactions/<int:txn_id>', methods=['PUT', 'PATCH'])
@login_required
def update_transaction(txn_id):
    try:
        data = request.get_json() or {}
        txn = next((t for t in transactions if t['id'] == txn_id), None)
        if not txn:
            return jsonify({'error': 'Not found'}), 404
        if 'dateTime' in data:
            txn['dateTime'] = data['dateTime']
        if 'amount' in data:
            txn['amount'] = data['amount']
        return jsonify(txn), 200
    except Exception:
        current_app.logger.exception('Error updating transaction')
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/transactions/<int:txn_id>', methods=['DELETE'])
@login_required
def delete_transaction(txn_id):
    global transactions
    transactions = [t for t in transactions if t['id'] != txn_id]
    return jsonify({'message': 'Deleted'}), 200


# --- New Analysis endpoints (JSON only) ---

@api_bp.route('/analysis/abtest', methods=['GET', 'POST'])
@login_required
def api_ab_test():
    """
    Returns:
      {
        "mean_a":   float,
        "mean_b":   float,
        "p_value":  float
      }
    """
    try:
        if request.method == 'POST':
            data = request.get_json(force=True) or {}
            group_by = data.get('group_by')
            param_a  = data.get('param_a')
            param_b  = data.get('param_b')

            if not group_by or not param_a or not param_b:
                return jsonify({'error': 'Missing parameters'}), 400

            result = run_ab_test(group_by, param_a, param_b)
        else:
            # fallback GET → run default test if needed
            result = run_ab_test()

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.exception("Error running A/B test")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analysis/regression', methods=['GET'])
@login_required
def api_regression():
    # 1) Parse period → hours filter
    period = request.args.get('period', 'all').lower()
    if period == 'morning':
        hours = list(range(0, 12))
    elif period == 'noon':
        hours = [12]
    elif period == 'afternoon':
        hours = list(range(13, 18))
    else:
        hours = None

    # 2) Parse date-range filters
    start_str = request.args.get('start')
    end_str   = request.args.get('end')
    start_dt = datetime.fromisoformat(start_str) if start_str else None
    end_dt   = datetime.fromisoformat(end_str)   if end_str   else None

    # 3) Rebuild (timestamp, amount) pairs
    pairs = []
    for t in transactions:
        raw = t.get('dateTime') or t.get('date')
        if not raw:
            continue

        # strip any trailing "T00:00" or extra offset
        if 'T' in raw:
            raw = raw.split('T', 1)[0]
        if raw.count(' ') > 1:
            raw = raw.rsplit(' ', 1)[0]

        # parse into datetime
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            try:
                dt = datetime.strptime(raw, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                current_app.logger.debug(f"Bad date {raw!r}: {e}")
                continue

        # apply filters
        if start_dt and dt < start_dt:
            continue
        if end_dt   and dt > end_dt:
            continue
        if hours    and dt.hour not in hours:
            continue

        pairs.append((dt.timestamp(), t['amount']))

    # 4) Compute regression stats
    stats = compute_regression(pairs)  # { intercept, slope, r_squared }

    # 5) Plot scatter + fit line
    xs = np.array([x for x,_ in pairs])
    ys = np.array([y for _,y in pairs])
    plt.figure()
    plt.scatter(xs, ys, alpha=0.6)
    plt.plot(xs, stats['intercept'] + stats['slope'] * xs, linewidth=2)
    plt.tight_layout()

    # 6) Encode to base64 PNG
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    chart_b64 = base64.b64encode(buf.read()).decode('ascii')

    # 7) Return JSON with stats + chart
    return jsonify({
        **stats,
        'chart_img': chart_b64
    }), 200