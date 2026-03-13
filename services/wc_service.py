from utils.safe_math import safe_divide, default_zero
import math


def calculate_wc_logic(data):

    # =====================================================
    # INPUT NORMALIZATION
    # =====================================================

    if isinstance(data, dict):

        if "inputs" in data:
            inputs = data.get("inputs", {})
            calc = data.get("calculations", {})
        else:
            inputs = data
            calc = {}

    else:
        inputs = {}
        calc = {}

    # =====================================================
    # EXTRACT FINANCIAL INPUTS
    # =====================================================

    inventory = default_zero(inputs.get("inventory"))

    receivables = default_zero(
        inputs.get("receivables") or inputs.get("sundry_debtors")
    )

    payables = default_zero(
        inputs.get("payables") or inputs.get("current_liabilities")
    )

    other_ca = default_zero(inputs.get("other_current_assets"))
    other_cl = default_zero(inputs.get("other_current_liabilities"))

    cash_bank = default_zero(inputs.get("cash_bank"))

    sales = default_zero(
        inputs.get("annual_sales") or inputs.get("sales")
    )

    cogs = default_zero(
        inputs.get("cogs") or inputs.get("cost_of_sales")
    )

    bank_credit = default_zero(inputs.get("bank_credit"))

    networth = default_zero(calc.get("networth"))
    total_debt = default_zero(calc.get("total_debt"))

    # =====================================================
    # CURRENT ASSETS / LIABILITIES RECONSTRUCTION
    # =====================================================

    ca = inventory + receivables + other_ca + cash_bank
    cl = payables + other_cl

    # If parser provided totals use them; prefer parser value if explicitly provided
    parser_ca = inputs.get("current_assets")
    parser_cl = inputs.get("current_liabilities")
    ca = default_zero(parser_ca) if parser_ca is not None else ca
    cl = default_zero(parser_cl) if parser_cl is not None else cl

    # =====================================================
    # AUTO COGS ESTIMATION
    # =====================================================

    if cogs == 0 and sales > 0:
        cogs = sales * 0.70

    # =====================================================
    # WORKING CAPITAL METRICS
    # =====================================================

    nwc = ca - cl

    current_ratio = safe_divide(ca, cl)
    quick_ratio = safe_divide((ca - inventory), cl)

    wc_turnover = safe_divide(sales, nwc)

    # =====================================================
    # OPERATING CYCLE
    # =====================================================

    inventory_days = safe_divide(inventory, cogs) * 365
    receivable_days = safe_divide(receivables, sales) * 365
    payable_days = safe_divide(payables, cogs) * 365

    operating_cycle = inventory_days + receivable_days
    gap_days = max(0, operating_cycle - payable_days)

    # =====================================================
    # DRAWING POWER (BANK METHOD)
    # =====================================================

    eligible_stock = inventory * 0.5
    eligible_debtors = receivables * 0.75

    drawing_power = eligible_stock + eligible_debtors - bank_credit
    drawing_power = max(0, drawing_power)

    # =====================================================
    # MPBF (TANDON METHOD)
    # =====================================================

    gca = inventory + receivables + other_ca
    total_cl = payables + other_cl

    wcg = gca - total_cl

    margin = gca * 0.25

    mpbf = wcg - margin

    # =====================================================
    # TURNOVER METHOD
    # =====================================================

    turnover_limit = sales * 0.20 if sales > 0 else 0

    if turnover_limit > 0 and mpbf > 0:
        recommended_limit = min(mpbf, turnover_limit)
    else:
        recommended_limit = max(mpbf, turnover_limit)

    # =====================================================
    # CHART DATA
    # =====================================================

    gap_chart = [
        {"name": "Gross Current Assets", "value": gca},
        {"name": "Current Liabilities", "value": total_cl},
        {"name": "Working Capital Gap", "value": wcg},
        {"name": "MPBF", "value": mpbf}
    ]

    composition_chart = [
        {"name": "Inventory", "value": inventory},
        {"name": "Receivables", "value": receivables},
        {"name": "Other CA", "value": other_ca}
    ]

    # =====================================================
    # RISK SCORING ENGINE
    # =====================================================

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

    # =====================================================
    # SAFE CLEAN FUNCTION
    # =====================================================

    def clean(value):

        if isinstance(value, float) and (
            math.isnan(value) or math.isinf(value)
        ):
            return 0

        return round(value, 2)

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "ratios": {
            "nwc": clean(nwc),
            "current_ratio": clean(current_ratio),
            "quick_ratio": clean(quick_ratio),
            "wc_turnover": clean(wc_turnover),
            "operating_cycle": clean(operating_cycle),
            "gap_days": clean(gap_days),
            "drawing_power": clean(drawing_power)
        },

        "mpbf_analysis": {
            "gca": clean(gca),
            "cl": clean(total_cl),
            "wcg": clean(wcg),
            "margin": clean(margin),
            "mpbf": clean(mpbf),
            "turnover_limit": clean(turnover_limit),
            "recommended_limit": clean(recommended_limit)
        },

        "capital_structure": {
            "networth": clean(networth),
            "total_debt": clean(total_debt)
        },

        "charts": {
            "gap_chart": gap_chart,
            "composition_chart": composition_chart
        },

        "risk": {
            "risk_score": risk_score,
            "risk_grade": risk_grade
        },

        "status": "Eligible" if nwc > 0 else "Not Eligible"
    }
