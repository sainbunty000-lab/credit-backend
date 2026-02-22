def safe(value):
    return float(value) if value is not None else 0.0


def calculate_working_capital(data):
    # Safe extraction
    current_assets = safe(data.get("current_assets"))
    current_liabilities = safe(data.get("current_liabilities"))
    capital = safe(data.get("capital"))
    reserves = safe(data.get("reserves"))
    unsecured_loans = safe(data.get("unsecured_loans"))
    investments = safe(data.get("investments"))
    loans_advances = safe(data.get("loans_advances"))
    fixed_assets = safe(data.get("fixed_assets"))
    creditors = safe(data.get("creditors"))
    annual_sales = safe(data.get("annual_sales"))
    purchases = safe(data.get("purchases"))
    stock = safe(data.get("stock"))
    debtors = safe(data.get("debtors"))
    tax = safe(data.get("tax"))

    # 1️⃣ Turnover Method
    turnover_eligibility = 0.20 * annual_sales

    # 2️⃣ NWC
    nwc = current_assets - current_liabilities

    # 3️⃣ WCG
    wcg = current_assets - creditors

    # 4️⃣ MPBF
    mpbf = (0.75 * wcg) - nwc
    if mpbf < 0:
        mpbf = 0

    # 5️⃣ Ratios
    current_ratio = (
        current_assets / current_liabilities
        if current_liabilities != 0
        else 0
    )

    net_worth = capital + reserves
    total_outside_liabilities = unsecured_loans + creditors + loans_advances

    leverage_ratio = (
        total_outside_liabilities / net_worth
        if net_worth != 0
        else 0
    )

    # Rule Checks
    current_ratio_status = "OK" if current_ratio >= 1.33 else "Below Required"
    leverage_status = "OK" if leverage_ratio <= 3 else "High"

    # Final Eligibility (Higher of two)
    final_eligibility = max(turnover_eligibility, mpbf)

    status = "Eligible" if final_eligibility > 0 else "Not Eligible"

    return {
        "turnover_method": {
            "annual_sales": annual_sales,
            "eligibility": round(turnover_eligibility, 2),
        },
        "nwc_method": {
            "nwc": round(nwc, 2),
            "wcg": round(wcg, 2),
            "mpbf": round(mpbf, 2),
        },
        "ratios": {
            "current_ratio": round(current_ratio, 2),
            "leverage_ratio": round(leverage_ratio, 2),
            "current_ratio_status": current_ratio_status,
            "leverage_status": leverage_status,
        },
        "final_eligible_amount": round(final_eligibility, 2),
        "logic_used": "Higher of Turnover or MPBF",
        "status": status,
    }
