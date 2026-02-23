from utils.safe_math import safe_divide, safe_subtract, default_zero

def calculate_wc_logic(data):

    ca = default_zero(data.get("current_assets"))
    cl = default_zero(data.get("current_liabilities"))
    sales = default_zero(data.get("annual_sales"))
    inventory = default_zero(data.get("inventory"))
    receivables = default_zero(data.get("trade_receivables"))
    payables = default_zero(data.get("trade_payables"))
    cogs = default_zero(data.get("cogs"))
    bank_credit_days = default_zero(data.get("bank_credit_days"))

    # Core
    nwc = safe_subtract(ca, cl)

    current_ratio = safe_divide(ca, cl)
    quick_ratio = safe_divide((ca - inventory), cl)
    wc_turnover = safe_divide(sales, nwc)

    # Days Calculations
    inventory_days = safe_divide(inventory, cogs) * 365
    receivable_days = safe_divide(receivables, sales) * 365
    payable_days = safe_divide(payables, cogs) * 365

    operating_cycle = inventory_days + receivable_days - payable_days
    gap_days = operating_cycle - bank_credit_days

    drawing_power = safe_subtract((0.75 * ca), cl)

    # Stress
    stressed_sales = sales * 0.8
    stressed_turnover = safe_divide(stressed_sales, nwc)

    # Liquidity Score
    score = 0

    if current_ratio > 1.5:
        score += 25
    elif current_ratio > 1.2:
        score += 15

    if quick_ratio > 1:
        score += 20

    if nwc > 0:
        score += 20

    if gap_days <= 0:
        score += 20

    if wc_turnover < 10:
        score += 15

    liquidity_status = (
        "Strong" if score >= 75
        else "Moderate" if score >= 50
        else "Weak"
    )

    return {
        "nwc": round(nwc, 2),
        "current_ratio": round(current_ratio, 2),
        "quick_ratio": round(quick_ratio, 2),
        "wc_turnover": round(wc_turnover, 2),
        "inventory_days": round(inventory_days, 2),
        "receivable_days": round(receivable_days, 2),
        "payable_days": round(payable_days, 2),
        "operating_cycle": round(operating_cycle, 2),
        "gap_days": round(gap_days, 2),
        "drawing_power": round(drawing_power, 2),
        "stressed_turnover": round(stressed_turnover, 2),
        "liquidity_score": score,
        "liquidity_status": liquidity_status
    }
