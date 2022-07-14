import numpy as np

def effective_bit_depth(img):
    return np.ceil(np.log2(np.max(img)))

def safe_normalize_max(array):
    m = np.max(array)
    if m:
        return np.divide(array, np.max(array))
    else:
        return np.full_like(array, np.NaN)
        

def safe_normalize_sum(array):
    s = np.sum(array)
    if s:
        return np.divide(array, np.sum(array))
    else:
        return np.full_like(array, np.NaN)
    