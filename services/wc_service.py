def safe(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def calculate_working_capital(data: dict):

    current_assets = safe(data.get("current_assets"))
    current_liabilities = safe(data.get("current_liabilities"))
    capital = safe(data.get("capital"))
    reserves = safe(data.get("reserves"))
    unsecured_loans = safe(data.get("unsecured_loans"))
    loans_advances = safe(data.get("loans_advances"))
    creditors = safe(data.get("creditors"))
    annual_sales = safe(data.get("annual_sales"))

    # Turnover Method (20%)
    turnover_eligibility = 0.20 * annual_sales

    # NWC
    nwc = current_assets - current_liabilities

    # Working Capital Gap
    wcg = current_assets - creditors

    # MPBF (2nd Method)
    mpbf = (0.75 * wcg) - nwc
    if mpbf < 0:
        mpbf = 0

    # Ratios
    current_ratio = current_assets / current_liabilities if current_liabilities != 0 else 0

    net_worth = capital + reserves
    total_outside_liabilities = unsecured_loans + loans_advances + creditors

    leverage_ratio = total_outside_liabilities / net_worth if net_worth != 0 else 0

    current_ratio_status = "OK" if current_ratio >= 1.33 else "Below Required"
    leverage_status = "OK" if leverage_ratio <= 3 else "High"

    final_eligibility = max(turnover_eligibility, mpbf)

    status = "Eligible" if final_eligibility > 0 else "Not Eligible"

    return {
        "turnover_method": round(turnover_eligibility, 2),
        "mpbf_method": round(mpbf, 2),
        "current_ratio": round(current_ratio, 2),
        "leverage_ratio": round(leverage_ratio, 2),
        "final_eligible_amount": round(final_eligibility, 2),
        "status": status
    }
