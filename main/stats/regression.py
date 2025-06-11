# main/stats/regression.py

import numpy as np
import statsmodels.api as sm
from datetime import datetime
from ..data import transactions   # ← pull from main/data.py

def compute_regression(pairs):
    """
    Expects a list of (x, y) tuples.
    Fits OLS: y = intercept + slope*x
    """
    if not pairs:
        return {'intercept': None, 'slope': None, 'r_squared': None}

    xs = np.array([x for x, _ in pairs])
    ys = np.array([y for _, y in pairs])
    X  = sm.add_constant(xs)
    model = sm.OLS(ys, X).fit()

    return {
        'slope':     float(model.params[1]),
        'intercept': float(model.params[0]),
        'r_squared': float(model.rsquared)
    }

def run_regression(start=None, end=None, months=None, hours=None):
    """
    Filter transactions by:
      - `start`, `end`: ISO date strings, e.g. "2025-06-01"
      - `months`:  list of ints 1–12 to include
      - `hours`:   list of ints 0–23 to include

    Returns the same dict as compute_regression().
    """
    # parse date filters once
    start_dt = datetime.fromisoformat(start) if start else None
    end_dt   = datetime.fromisoformat(end)   if end   else None

    pairs = []
    for t in transactions:
        dt_str = t.get('dateTime') or t.get('date')
        if not dt_str:
            continue
        # assume ISO format "YYYY-MM-DDTHH:MM"
        dt = datetime.fromisoformat(dt_str)

        # apply date range filter
        if start_dt and dt < start_dt:
            continue
        if end_dt and dt > end_dt:
            continue

        # apply month filter
        if months and dt.month not in months:
            continue

        # apply hour-of-day filter
        if hours and dt.hour not in hours:
            continue

        # build (x, y) pair: x = timestamp, y = amount
        pairs.append((dt.timestamp(), t['amount']))

    return compute_regression(pairs)
