from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from .data import transactions
from auth.utils import login_required

main_bp = Blueprint('main', __name__, template_folder='../templates')

@main_bp.route('/transactions')
@login_required
def get_transactions():
    total = sum(t['amount'] for t in transactions)
    return render_template('transactions.html',
                           transactions=transactions,
                           total_amount=total)

@main_bp.route('/add', methods=['GET','POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            date_str = request.form['date']
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            amt = float(request.form['amount'])
            transactions.append({
                'id': len(transactions) + 1,
                'date': dt.strftime('%Y-%m-%d'),
                'amount': amt
            })
            return redirect(url_for('main.get_transactions'))
        except ValueError:
            return "Invalid input", 400
    return render_template('form.html')

@main_bp.route('/edit/<int:transaction_id>', methods=['GET','POST'])
@login_required
def edit_transaction(transaction_id):
    txn = next((t for t in transactions if t['id'] == transaction_id), None)
    if not txn:
        return {"message": "Not found"}, 404

    if request.method == 'POST':
        txn['date'] = request.form['date']
        txn['amount'] = float(request.form['amount'])
        return redirect(url_for('main.get_transactions'))

    return render_template('edit.html', transaction=txn)

@main_bp.route('/delete/<int:transaction_id>')
@login_required
def delete_transaction(transaction_id):
    global transactions
    transactions[:] = [t for t in transactions if t['id'] != transaction_id]
    return redirect(url_for('main.get_transactions'))

@main_bp.route('/search', methods=['GET','POST'])
@login_required
def search_transactions():
    if request.method == 'POST':
        try:
            lo = float(request.form['min_amount'])
            hi = float(request.form['max_amount'])
            results = [t for t in transactions if lo <= t['amount'] <= hi]
            total = sum(t['amount'] for t in results)
            return render_template('transactions.html',
                                   transactions=results,
                                   total_amount=total)
        except ValueError:
            return "Invalid input", 400
    return render_template('search.html')