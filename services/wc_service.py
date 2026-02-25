from utils.safe_math import safe_divide, safe_subtract, default_zero

def calculate_wc_logic(data):

    ca = float(data.get("current_assets", 0))
    cl = float(data.get("current_liabilities", 0))
    inventory = float(data.get("inventory", 0))
    receivables = float(data.get("receivables", 0))
    payables = float(data.get("payables", 0))
    sales = float(data.get("annual_sales", 0))
    cogs = float(data.get("cogs", 0))
    bank_credit = float(data.get("bank_credit", 0))

    nwc = safe_subtract(ca, cl)
    current_ratio = safe_divide(ca, cl)
quick_ratio = safe_divide(ca - inventory, cl)
wc_turnover = safe_divide(sales, nwc)
inventory_days = safe_divide(inventory, cogs) * 365
receivable_days = safe_divide(receivables, sales) * 365
payable_days = safe_divide(payables, cogs) * 365

    operating_cycle = inventory_days + receivable_days
    gap_days = operating_cycle - payable_days

    drawing_power = (receivables * 0.75) + (inventory * 0.5) - bank_credit

    liquidity_score = 90 if current_ratio >= 2 else 70 if current_ratio >= 1.5 else 50

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
        "liquidity_score": liquidity_score,
        "status": "Eligible" if nwc > 0 else "Not Eligible"
    }
