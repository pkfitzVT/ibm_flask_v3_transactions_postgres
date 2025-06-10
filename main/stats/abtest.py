import numpy as np
from scipy import stats

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
    # If one group is empty, we cannot compute a test
    if not groupA or not groupB:
        return None
    # SciPy returns a statistic and pvalue; we only want pvalue
    stat, pvalue = stats.ttest_ind(groupA, groupB, equal_var=False)
    return float(pvalue)
