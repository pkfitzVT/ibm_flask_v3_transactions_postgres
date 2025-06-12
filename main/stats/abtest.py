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

def run_ab_test(group_by, param_a, param_b):
    # TEMP: Just return params to test flow
    return {
        'group_by': group_by,
        'param_a': param_a,
        'param_b': param_b,
        'mean_a': 0,
        'mean_b': 0,
        'p_value': 1.0
    }

