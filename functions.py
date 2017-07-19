import numpy as np

def p2f(x):
    try:
        return float(x.rstrip('%'))
    except:
        return np.nan