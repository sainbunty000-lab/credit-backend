from utils.safe_math import safe_divide, safe_subtract, default_zero
import math

def calculate_wc_logic(data):

    ca = default_zero(data.get("current_assets"))
    cl = default_zero(data.get("current_liabilities"))
    inventory = default_zero(data.get("inventory"))
    receivables = default_zero(data.get("receivables"))
    payables = default_zero(data.get("payables"))
    sales = default_zero(data.get("annual_sales"))
    cogs = default_zero(data.get("cogs"))
    bank_credit = default_zero(data.get("bank_credit"))

    nwc = ca - cl

    current_ratio = safe_divide(ca, cl)
    quick_ratio = safe_divide((ca - inventory), cl)
    wc_turnover = safe_divide(sales, nwc)

    inventory_days = safe_divide(inventory, cogs) * 365
    receivable_days = safe_divide(receivables, sales) * 365
    payable_days = safe_divide(payables, cogs) * 365

    operating_cycle = inventory_days + receivable_days
    gap_days = operating_cycle - payable_days

    drawing_power = (receivables * 0.75) + (inventory * 0.5) - bank_credit

    liquidity_score = 90 if current_ratio >= 2 else 70 if current_ratio >= 1.5 else 50

    # Prevent JSON errors (remove NaN / inf)
    def clean(value):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return 0
        return round(value, 2)

    return {
        "nwc": clean(nwc),
        "current_ratio": clean(current_ratio),
        "quick_ratio": clean(quick_ratio),
        "wc_turnover": clean(wc_turnover),
        "inventory_days": clean(inventory_days),
        "receivable_days": clean(receivable_days),
        "payable_days": clean(payable_days),
        "operating_cycle": clean(operating_cycle),
        "gap_days": clean(gap_days),
        "drawing_power": clean(drawing_power),
        "liquidity_score": liquidity_score,
        "status": "Eligible" if nwc > 0 else "Not Eligible"
    }

    # ============================
    # EXISTING RATIO ENGINE
    # ============================
    nwc = ca - cl
    current_ratio = safe_divide(ca, cl)
    quick_ratio = safe_divide((ca - inventory), cl)
    wc_turnover = safe_divide(sales, nwc)

    inventory_days = safe_divide(inventory, cogs) * 365
    receivable_days = safe_divide(receivables, sales) * 365
    payable_days = safe_divide(payables, cogs) * 365

    operating_cycle = inventory_days + receivable_days
    gap_days = operating_cycle - payable_days

    drawing_power = (receivables * 0.75) + (inventory * 0.5) - bank_credit

    # ============================
    # MPBF METHOD (BANK STANDARD)
    # ============================
    stock = inventory
    debtors = receivables
    gca = stock + debtors + other_ca
    total_cl = payables + other_cl

    wcg = gca - total_cl

    margin_percent = 0.25  # 25% borrower contribution
    margin = gca * margin_percent

    mpbf = wcg - margin

    # ============================
    # TURNOVER METHOD (ALT METHOD)
    # ============================
    turnover_limit = sales * 0.20  # 20% of turnover

    # ============================
    # FINAL RECOMMENDATION
    # ============================
    recommended_limit = min(mpbf, turnover_limit)

    # ============================
    # ASSET COMPOSITION %
    # ============================
    asset_composition = {
        "stock_percent": safe_divide(stock, gca) * 100,
        "debtors_percent": safe_divide(debtors, gca) * 100,
        "other_ca_percent": safe_divide(other_ca, gca) * 100
    }

    # ============================
    # CHART READY DATA
    # ============================
    gap_chart = [
        {"name": "GCA", "value": gca},
        {"name": "CL", "value": total_cl},
        {"name": "WCG", "value": wcg},
        {"name": "MPBF", "value": mpbf}
    ]

    composition_chart = [
        {"name": "Stock", "value": stock},
        {"name": "Debtors", "value": debtors},
        {"name": "Other CA", "value": other_ca}
    ]

    # ============================
    # RISK GRADING
    # ============================
    risk_score = 0

    if current_ratio >= 2:
        risk_score += 30
    elif current_ratio >= 1.5:
        risk_score += 20
    else:
        risk_score += 10

    if mpbf > 0:
        risk_score += 30

    if gap_days < 120:
        risk_score += 20

    if wc_turnover > 3:
        risk_score += 20

    risk_grade = (
        "A" if risk_score >= 80 else
        "B" if risk_score >= 60 else
        "C" if risk_score >= 40 else
        "D"
    )

    # ============================
    # STRUCTURED RETURN
    # ============================
    return {
        "input": data,
        "ratios": {
            "nwc": round(nwc, 2),
            "current_ratio": round(current_ratio, 2),
            "quick_ratio": round(quick_ratio, 2),
            "wc_turnover": round(wc_turnover, 2),
            "operating_cycle": round(operating_cycle, 2),
            "gap_days": round(gap_days, 2),
            "drawing_power": round(drawing_power, 2)
        },
        "mpbf_analysis": {
            "gca": round(gca, 2),
            "cl": round(total_cl, 2),
            "wcg": round(wcg, 2),
            "margin": round(margin, 2),
            "mpbf": round(mpbf, 2),
            "turnover_limit": round(turnover_limit, 2),
            "recommended_limit": round(recommended_limit, 2)
        },
        "charts": {
            "gap_chart": gap_chart,
            "composition_chart": composition_chart
        },
        "risk": {
            "risk_score": risk_score,
            "risk_grade": risk_grade
        }
    }
