# main/api_routes.py

from flask import Blueprint, jsonify, request, session, current_app
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from .data import transactions            # in-memory transaction list
from auth.routes import users             # in-memory users list
from auth.utils import login_required     # session validator

api_bp = Blueprint('api', __name__, url_prefix='/api')
# enable CORS on this blueprint
CORS(
    api_bp,
    supports_credentials=True,
    origins="http://localhost:3000",
    methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"]
)

# --- Auth endpoints ---

@api_bp.route('/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    email = data.get('email')
    pwd   = data.get('password')
    if not email or not pwd:
        return jsonify({'error': 'Missing email or password'}), 400
    if any(u['email'] == email for u in users):
        return jsonify({'error': 'Email already registered'}), 400

    pw_hash = generate_password_hash(pwd)
    new_user = {'id': len(users) + 1, 'email': email, 'pw_hash': pw_hash}
    users.append(new_user)
    return jsonify({'message': 'Registered successfully'}), 201

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
        dt = data.get('dateTime')
        amt = data.get('amount')
        if not dt or amt is None:
            return jsonify({'error': 'Missing dateTime or amount'}), 400
        # Compute a unique ID using the max existing id
        max_id = max((t['id'] for t in transactions), default=0)
        new_txn = {'id': max_id + 1, 'dateTime': dt, 'amount': amt}
        transactions.append(new_txn)
        return jsonify(new_txn), 201
    except Exception as e:
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
    except Exception as e:
        current_app.logger.exception('Error updating transaction')
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/transactions/<int:txn_id>', methods=['DELETE'])
@login_required
def delete_transaction(txn_id):
    global transactions
    transactions = [t for t in transactions if t['id'] != txn_id]
    return jsonify({'message': 'Deleted'}), 200
