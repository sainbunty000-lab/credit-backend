import math


# ==========================================================
# SAFE DIVISION
# ==========================================================

def safe_divide(n, d):

    try:

        n = normalize_number(n)
        d = normalize_number(d)

        if d == 0:
            return 0

        return n / d
    except Exception:
        return 0


# ==========================================================
# SAFE SUBTRACTION
# Prevent negative results if required
# ==========================================================

def safe_subtract(a, b, allow_negative=False):

    try:

        a = normalize_number(a)
        b = normalize_number(b)

        result = a - b

        if not allow_negative:
            return max(0, result)

        return result
    except Exception:
        return 0


# ==========================================================
# SAFE ADDITION
# ==========================================================

def safe_add(a, b):

    try:
        return normalize_number(a) + normalize_number(b)
    except Exception:
        return 0


# ==========================================================
# SAFE MULTIPLY
# ==========================================================

def safe_multiply(a, b):

    try:
        return normalize_number(a) * normalize_number(b)
    except Exception:
        return 0


# ==========================================================
# DEFAULT ZERO
# Converts anything into safe float
# ==========================================================

def default_zero(val):

    try:

        if val is None:
            return 0.0

        val = str(val)
        val = val.replace(",", "")
        val = val.replace('₹', '')
        val = val.strip()
        if val == "":
            return 0.0

        num = float(val)

        if math.isnan(num) or math.isinf(num):
            return 0.0

        return num
    except Exception:
        return 0.0


# ==========================================================
# NORMALIZE NUMBER
# Internal helper
# ==========================================================

def normalize_number(val):

    if val is None:
        return 0.0

    try:

        val = str(val)
        val = val.replace(",", "")
        val = val.replace('₹', '')
        val = val.strip()
        if val == "":
            return 0.0

        num = float(val)

        if math.isnan(num) or math.isinf(num):
            return 0.0

        return num
    except Exception:
        return 0.0
