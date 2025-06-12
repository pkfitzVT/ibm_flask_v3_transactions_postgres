import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
from .data import transactions
import scipy.stats as stats

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
    Returns the p-value.
    """
    if not groupA or not groupB:
        return None
    _, pvalue = stats.ttest_ind(groupA, groupB, equal_var=False)
    return float(pvalue)

def run_ab_test(group_by='half', param_a='1', param_b='2'):
    """
    Run A/B test on transactions based on selected grouping.

    Parameters:
    - group_by: str ('half', 'weekday', 'time', 'month')
    - param_a: str → Group A value (meaning depends on group_by)
    - param_b: str → Group B value (meaning depends on group_by)

    Returns:
    Dict with:
    - groupA (list of amounts)
    - groupB (list of amounts)
    - p_value (float)
    - boxplot_img (base64 PNG image)
    """

    # Helper to parse transaction dateTime safely
    def parse_txn_datetime(t):
        raw = t.get('dateTime') or t.get('date')
        if not raw:
            return None
        # Strip T00:00 if present
        if 'T' in raw:
            raw = raw.split('T')[0]
        try:
            dt = datetime.fromisoformat(raw)
            return dt
        except Exception:
            return None

    # Build Group A and Group B
    groupA = []
    groupB = []

    for t in transactions:
        dt = parse_txn_datetime(t)
        if not dt:
            continue  # skip bad date

        # Determine group membership based on group_by
        match group_by:
            case 'half':
                # First half vs. second half by transaction order
                # We'll use index in list as proxy
                index = transactions.index(t)
                midpoint = len(transactions) // 2
                txn_group = '1' if index < midpoint else '2'
            case 'weekday':
                # Monday=0, Sunday=6 → convert to str for param comparison
                txn_group = str(dt.weekday())
            case 'time':
                # Map hour → time of day bucket
                hour = dt.hour
                if 6 <= hour <= 11:
                    txn_group = 'morning'
                elif 12 <= hour <= 17:
                    txn_group = 'afternoon'
                elif 18 <= hour <= 23:
                    txn_group = 'evening'
                else:
                    txn_group = 'night'
            case 'month':
                txn_group = str(dt.month)
            case _:
                # Unknown group_by → skip
                continue

        # Assign to Group A or Group B based on param_a / param_b
        amount = t['amount']
        if txn_group == param_a:
            groupA.append(amount)
        elif txn_group == param_b:
            groupB.append(amount)
        else:
            continue  # transaction does not match either group → skip

    # Clean outliers
    groupA_clean = remove_outliers(groupA)
    groupB_clean = remove_outliers(groupB)

    # Compute p-value
    p_val = t_test(groupA_clean, groupB_clean)

    # Create boxplot
    plt.figure(figsize=(6,4))
    plt.boxplot([groupA_clean, groupB_clean], labels=['Group A', 'Group B'])
    plt.title(f"A/B Test — {group_by}: {param_a} vs {param_b}")
    plt.tight_layout()

    # Encode boxplot as base64 PNG
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    boxplot_b64 = base64.b64encode(buf.read()).decode('ascii')

    # Return result
    return {
        'groupA': groupA_clean,
        'groupB': groupB_clean,
        'p_value': p_val,
        'boxplot_img': boxplot_b64
    }
