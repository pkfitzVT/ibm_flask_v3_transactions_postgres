import numpy as np
import statsmodels.api as sm

def compute_regression(pairs):
    xs = np.array([x for x,_ in pairs])
    ys = np.array([y for _,y in pairs])
    X  = sm.add_constant(xs)
    model = sm.OLS(ys, X).fit()
    return {
        'slope':     float(model.params[1]),
        'intercept': float(model.params[0]),
        'r2':        float(model.rsquared)
    }
