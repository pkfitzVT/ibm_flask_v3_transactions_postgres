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

@main_bp.route('/analysis/regression', methods=['GET','POST'])
@login_required
def regression():
    # Default filter values
    start = request.values.get('start_date', '2024-01-01')
    end   = request.values.get('end_date',   '2024-12-31')
    period = request.values.get('period', 'all')  # morning/noon/afternoon/all

    # Parse dates
    start_dt = datetime.fromisoformat(start)
    end_dt   = datetime.fromisoformat(end)

    # Filter transactions by date AND time-of-day
    filtered = []
    for t in transactions:
        dt = t['date'] if isinstance(t['date'], datetime) else datetime.fromisoformat(t['date'])
        if not (start_dt <= dt <= end_dt):
            continue
        if period == 'morning'   and dt.hour != 9:   continue
        if period == 'noon'      and dt.hour != 12:  continue
        if period == 'afternoon' and dt.hour != 16:  continue
        filtered.append((dt.timestamp(), t['amount']))  # x = timestamp, y = amount

    # Compute regression on timestamp vs. amount
    result = compute_regression(filtered) if filtered else {}

    # Prepare image (optional Matplotlib code here, or skip for Chart.js)
    # ...

    return render_template(
        'regression.html',
        start=start,
        end=end,
        period=period,
        result=result,
        # chart_img=img_data,
        # or filtered_points=json.dumps([...]) for JS
    )