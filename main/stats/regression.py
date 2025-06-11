# main/stats/regression.py

import numpy as np
import statsmodels.api as sm
from datetime import datetime
from ..data import transactions

import matplotlib.pyplot as plt
import io, base64



def compute_regression(pairs):
    """
    Expects a list of (x, y) tuples.
    Fits OLS: y = intercept + slope * x
    Returns a dict with keys 'intercept', 'slope', and 'r_squared'.
    """
    if not pairs:
        return {'intercept': None, 'slope': None, 'r_squared': None}

    xs = np.array([x for x, _ in pairs])
    ys = np.array([y for _, y in pairs])
    X  = sm.add_constant(xs)
    model = sm.OLS(ys, X).fit()

    return {
        'intercept': float(model.params[0]),
        'slope':     float(model.params[1]),
        'r_squared': float(model.rsquared)
    }

def run_regression(start=None, end=None, months=None, hours=None):
    """
    1. Optionally filter transactions by:
         - start: ISO date string 'YYYY-MM-DD'
         - end:   ISO date string 'YYYY-MM-DD'
         - months: list of ints 1–12
         - hours:  list of ints 0–23
    2. Build (timestamp, amount) pairs
    3. Call compute_regression and return its result
    """
    # Parse date filters
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt   = datetime.fromisoformat(end)   if end   else None

    pairs = []
    for t in transactions:
        raw = t.get('dateTime') or t.get('date')
        if not raw:
            continue

        # === normalize timestamp ===
        # If there's a 'T' with extra data (e.g. "…T00:00"), drop it:
        if 'T' in raw:
            raw = raw.split('T', 1)[0]

        # If there's still a stray space + offset (e.g. "YYYY-MM-DD HH:MM:SS 00:00"), drop trailing part:
        if ' ' in raw and raw.count(' ') > 1:
            raw = raw.rsplit(' ', 1)[0]

        # Now raw should look like "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            # fallback to explicit strptime if needed
            try:
                dt = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                print(f"❌ Couldn't parse date string {raw!r}: {e}")
                continue

        # === apply filters ===
        if start_dt and dt < start_dt:
            continue
        if end_dt   and dt > end_dt:
            continue
        if months and dt.month not in months:
            continue
        if hours  and dt.hour  not in hours:
            continue

        pairs.append((dt.timestamp(), t['amount']))

    # Compute and return regression stats
    return compute_regression(pairs)
def make_chart(pairs, stats):
    # unpack stats
    intercept, slope = stats['intercept'], stats['slope']

    # get xs and ys
    xs = np.array([x for x, _ in pairs])
    ys = np.array([y for _, y in pairs])

    # plot scatter + line
    plt.figure()
    plt.scatter(xs, ys)
    plt.plot(xs, intercept + slope * xs, linewidth=2)
    plt.tight_layout()

    # encode to PNG/base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('ascii')