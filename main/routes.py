from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime
from .data import transactions
from auth.utils import login_required

from .stats.regression import compute_regression
from .stats.abtest     import remove_outliers, t_test
import json

from datetime import datetime

from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
import matplotlib.dates as mdates

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

@main_bp.route('/analysis')
@login_required
def analysis():
    return render_template('analysis.html')



@main_bp.route('/analysis/regression', methods=['GET','POST'])
@login_required
def regression():
    # 1) Read inputs
    start  = request.values.get('start_date', '2024-01-01')
    end    = request.values.get('end_date',   '2024-12-31')
    period = request.values.get('period',     'all')

    # 2) Parse dates
    start_dt = datetime.fromisoformat(start)
    end_dt   = datetime.fromisoformat(end)



    # 3) Filter, keeping datetime objects (not timestamps)
    filtered = []
    for t in transactions:
        dt = t['date'] if isinstance(t['date'], datetime) else datetime.fromisoformat(t['date'])
        if not (start_dt <= dt <= end_dt):
            continue
        if period == 'morning'   and not (6  <= dt.hour < 12): continue
        if period == 'noon'      and not (12 <= dt.hour < 14): continue
        if period == 'afternoon' and not (14 <= dt.hour < 18): continue
        filtered.append((dt, t['amount']))

    # 4) Compute regression
    dates = [dt for dt, amt in filtered]
    amounts = [amt for dt, amt in filtered]
    timestamps = [dt.timestamp() for dt in dates]

    # compute regression on timestamp vs amount
    if len(set(timestamps)) > 1 and len(set(amounts)) > 1:
        result = compute_regression(list(zip(timestamps, amounts)))
    else:
        result = {}

    chart_img = None
    if dates and amounts and 'slope' in result and 'intercept' in result:
        fig, ax = plt.subplots()

        # scatter with real dates
        ax.scatter(dates, amounts, alpha=0.6, label='Data')

        # compute fitted y = m * (dt.timestamp()) + b
        fit_y = [result['slope'] * ts + result['intercept'] for ts in timestamps]
        ax.plot(dates, fit_y, '-', label='Fit')

        # format x-axis as dates
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(mdates.AutoDateLocator()))
        fig.autofmt_xdate()

        ax.set_xlabel('Date')
        ax.set_ylabel('Amount')
        ax.set_title('Regression: Data & Trend Line')
        ax.legend()

        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        chart_img = base64.b64encode(buf.read()).decode('ascii')
    # 6) Render
    return render_template(
        'regression.html',
        start=start,
        end=end,
        period=period,
        result=result,
        chart_img=chart_img
    )



TIME_RANGES = {
    "morning":   range(6, 12),
    "afternoon": range(12, 18),
    "evening":   range(18, 24),
    "night":     range(0, 6),
}

@main_bp.route('/analysis/abtest', methods=['GET','POST'])
@login_required
def abtest_api():
    # 1) read your grouping choice
    group_by = request.values.get('group_by', 'half')
    paramA   = request.values.get('paramA', None)
    paramB   = request.values.get('paramB', None)

    # 2) parse all txns into (datetime, amount) pairs
    parsed = []
    for t in transactions:
        dt = t['date'] if isinstance(t['date'], datetime) else datetime.fromisoformat(t['date'])
        parsed.append((dt, t['amount']))

    # 3) bucket into two lists
    if group_by == 'weekday':
        a_list = [amt for dt, amt in parsed if dt.weekday() < 5]
        b_list = [amt for dt, amt in parsed if dt.weekday() >= 5]

    elif group_by == 'timeofday' and paramA in TIME_RANGES and paramB in TIME_RANGES:
        a_list = [amt for dt, amt in parsed if dt.hour in TIME_RANGES[paramA]]
        b_list = [amt for dt, amt in parsed if dt.hour in TIME_RANGES[paramB]]

    elif group_by == 'month' and paramA and paramB:
        mA = int(paramA); mB = int(paramB)
        a_list = [amt for dt, amt in parsed if dt.month == mA]
        b_list = [amt for dt, amt in parsed if dt.month == mB]

    else:
        # fallback to “first half vs second half”:
        amounts = [amt for _, amt in parsed]
        mid     = len(amounts) // 2
        a_list = amounts[:mid]
        b_list = amounts[mid:]

    # 4) run your existing outlier removal & t-test
    a = remove_outliers(a_list)
    b = remove_outliers(b_list)
    p = t_test(a, b)

    # ── generate boxplot ────────────────────────────────────────────────
    fig, ax = plt.subplots()
    ax.boxplot([a, b], labels=['Group A', 'Group B'])
    ax.set_title('A/B Test Boxplot')

    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    boxplot_img = base64.b64encode(buf.read()).decode('ascii')

    # 5) render, passing back your params so the form stays in sync
    return render_template(
        'ab_test.html',
        groupA=a,
        groupB=b,
        p_value=p,
        boxplot_img=boxplot_img,
        group_by=group_by,
        paramA=paramA,
        paramB=paramB
    )