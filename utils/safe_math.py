def safe_divide(numerator, denominator, default=0):
    try:
        if not denominator or denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default

def safe_subtract(a, b):
    res = (a or 0) - (b or 0)
    return max(0, res)  # Rule: Negative results -> 0

def default_zero(value):
    return value if value is not None else 0
