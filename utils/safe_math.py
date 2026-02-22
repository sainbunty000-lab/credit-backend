def default_zero(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_divide(a, b):
    return a / b if b != 0 else 0


def safe_subtract(a, b):
    return a - b
