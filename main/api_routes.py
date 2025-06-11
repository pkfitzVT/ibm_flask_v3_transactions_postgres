# main/api_routes.py

from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from .data import transactions
from auth.routes import users           # your in-memory users list
from auth.utils import login_required   # stub or real checker

api_bp = Blueprint('api', __name__, url_prefix='/api')

#
# Auth endpoints (JSON)
#

@api_bp.route('/register', methods=['POST'])
def api_register():
    data = request.get_json()
    email = data.get('email')
    pwd   = data.get('password')
    if any(u['email'] == email for u in users):
        return jsonify({'error': 'Email already registered'}), 400

    pw_hash = generate_password_hash(pwd)
    new_user = {'id': len(users) + 1, 'email': email, 'pw_hash': pw_hash}
    users.append(new_user)
    return jsonify({'message': 'Registered successfully'}), 201

@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()
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

#
# Transactions endpoints (JSON)
#

@api_bp.route('/transactions', methods=['GET'])
@login_required
def list_transactions():
    return jsonify(transactions), 200

@api_bp.route('/transactions', methods=['POST'])
@login_required
def create_transaction():
    data = request.get_json()
    # Expect { date: 'YYYY-MM-DD', amount: 123.45 }
    new_txn = {
        'id': len(transactions) + 1,
        'date': data['date'],
        'amount': data['amount']
    }
    transactions.append(new_txn)
    return jsonify(new_txn), 201

@api_bp.route('/transactions/<int:txn_id>', methods=['PUT', 'PATCH'])
@login_required
def update_transaction(txn_id):
    data = request.get_json()
    txn = next((t for t in transactions if t['id'] == txn_id), None)
    if not txn:
        return jsonify({'error': 'Not found'}), 404
    txn.update(data)
    return jsonify(txn), 200

@api_bp.route('/transactions/<int:txn_id>', methods=['DELETE'])
@login_required
def delete_transaction(txn_id):
    global transactions
    transactions = [t for t in transactions if t['id'] != txn_id]
    return jsonify({'message': 'Deleted'}), 200
