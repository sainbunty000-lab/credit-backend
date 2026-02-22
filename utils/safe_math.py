def safe_divide(n, d):
    try:
        return n / d if d and d != 0 else 0
    except:
        return 0

def safe_subtract(a, b):
    res = (a or 0) - (b or 0)
    return max(0, res)

def default_zero(val):
    try:
        return float(val) if val else 0.0
    except:
        return 0.0
