import base64
import io
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

from ..data import transactions


def remove_outliers(data):
    """
    Remove outliers from a list of numeric values using the 1.5*IQR rule.
    """
    if not data:
        return []
    arr = np.array(data)
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return [float(x) for x in arr if lower <= x <= upper]


def t_test(groupA, groupB):
    """
    Perform a two-sample t-test (unequal variance) between two lists of values.
    Returns a tuple: (t_statistic, p-value).
    """
    if not groupA or not groupB:
        return None, None
    t_stat, pvalue = stats.ttest_ind(groupA, groupB, equal_var=False)
    return float(t_stat), float(pvalue)


def run_ab_test(group_by="half", param_a="1", param_b="2"):
    """
    Run A/B test on transactions based on selected grouping.

    Returns a dict with:
    - groupA: list of cleaned values
    - groupB: list of cleaned values
    - t_score: float
    - p_value: float
    - boxplot_img: base64 PNG
    """

    def parse_txn_datetime(t):
        raw = t.get("dateTime") or t.get("date")
        if not raw:
            return None
        # If it's already a datetime object, return it directly
        if isinstance(raw, datetime):
            return raw
        # Ensure we have a full ISO timestamp
        s = raw
        if "T" not in s:
            s = f"{s}T00:00:00"
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            return None

    groupA = []
    groupB = []

    for t in transactions:
        dt = parse_txn_datetime(t)
        if not dt:
            continue

        # Determine grouping key
        # Determine grouping key
        if group_by == "half":
            idx = transactions.index(t)
            mid = len(transactions) // 2
            txn_group = "1" if idx < mid else "2"
        elif group_by == "weekday":
            txn_group = str(dt.weekday())
        elif group_by == "time":
            h = dt.hour
            if 6 <= h <= 11:
                txn_group = "morning"
            elif 12 <= h <= 17:
                txn_group = "afternoon"
            elif 18 <= h <= 23:
                txn_group = "evening"
            else:
                txn_group = "night"
        elif group_by == "month":
            txn_group = str(dt.month)
        else:
            continue

        amt = t.get("amount", 0)
        if txn_group == param_a:
            groupA.append(amt)
        elif txn_group == param_b:
            groupB.append(amt)

    groupA_clean = remove_outliers(groupA)
    groupB_clean = remove_outliers(groupB)

    # Compute t-statistic AND p-value
    t_stat, p_val = t_test(groupA_clean, groupB_clean)

    # Create boxplot
    plt.figure(figsize=(6, 4))
    plt.boxplot([groupA_clean, groupB_clean], labels=["Group A", "Group B"])
    plt.title(f"A/B Test — {group_by}: {param_a} vs {param_b}")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    boxplot_b64 = base64.b64encode(buf.read()).decode("ascii")

    return {
        "groupA": groupA_clean,
        "groupB": groupB_clean,
        "t_score": t_stat,
        "p_value": p_val,
        "boxplot_img": boxplot_b64,
    }
