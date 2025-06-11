# main/stats/abtest.py
import numpy as np
from scipy import stats

# import the shared transactions list from main/data.py
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
    Returns the p-value.
    """
    if not groupA or not groupB:
        return None
    _, pvalue = stats.ttest_ind(groupA, groupB, equal_var=False)
    return float(pvalue)

def run_ab_test():
    """
    1. Pull all transaction amounts
    2. Clean via remove_outliers()
    3. Split into two groups (first half vs. second half by timestamp/order)
    4. Compute means & p-value
    5. Return a dict for JSONifying
    """
    # Extract and clean
    amounts = [t['amount'] for t in transactions]
    cleaned = remove_outliers(amounts)

    # Split into two groups (customize this logic as you like)
    mid = len(cleaned) // 2
    groupA = cleaned[:mid]
    groupB = cleaned[mid:]

    # Compute summary stats
    mean_a = float(np.mean(groupA)) if groupA else None
    mean_b = float(np.mean(groupB)) if groupB else None
    p_val  = t_test(groupA, groupB)

    return {
        'mean_a':  mean_a,
        'mean_b':  mean_b,
        'p_value': p_val
    }
