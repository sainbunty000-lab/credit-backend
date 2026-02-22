def safe(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


# ---------------------------
# WORKING CAPITAL CALCULATION
# ---------------------------
def calculate_working_capital_detailed(data: dict):

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

    # MPBF Method
    nwc = current_assets - current_liabilities
    wcg = current_assets - creditors
    mpbf = (0.75 * wcg) - nwc
    if mpbf < 0:
        mpbf = 0

    # Ratios
    current_ratio = current_assets / current_liabilities if current_liabilities != 0 else 0

    net_worth = capital + reserves
    total_outside_liabilities = unsecured_loans + loans_advances + creditors
    leverage_ratio = total_outside_liabilities / net_worth if net_worth != 0 else 0

    final_eligible = max(turnover_eligibility, mpbf)
    status = "Eligible" if final_eligible > 0 else "Not Eligible"

    return {
        "turnover_method": {
            "eligible_amount": round(turnover_eligibility, 2)
        },
        "mpbf_method": {
            "eligible_amount": round(mpbf, 2)
        },
        "ratios": {
            "current_ratio": round(current_ratio, 2),
            "leverage_ratio": round(leverage_ratio, 2)
        },
        "final_decision": {
            "final_eligible_amount": round(final_eligible, 2),
            "status": status
        }
    }


# ---------------------------
# AGRICULTURE CALCULATION
# (YOUR CUSTOM RULE)
# ---------------------------
def calculate_agri_eligibility(data: dict):

    total_income = safe(data.get("total_income"))
    tax = safe(data.get("tax"))
    monthly_emi = safe(data.get("monthly_emi"))

    annual_emi = monthly_emi * 12

    # Step 1
    documented_income = (0.70 * total_income) - tax

    # Step 2
    undocumented_income = 0.60 * (0.70 * total_income)

    # Step 3
    total_net_income = documented_income + undocumented_income - annual_emi

    if total_net_income < 0:
        total_net_income = 0

    # Step 4
    eligibility_rupees = total_net_income / 0.14 if total_net_income > 0 else 0
    eligibility_lakhs = eligibility_rupees / 100000

    status = "Eligible" if eligibility_rupees > 0 else "Not Eligible"

    return {
        "inputs": {
            "total_income_rupees": total_income,
            "tax_rupees": tax,
            "monthly_emi_rupees": monthly_emi,
            "annual_emi_rupees": annual_emi
        },
        "calculation": {
            "documented_income_rupees": round(documented_income, 2),
            "undocumented_income_rupees": round(undocumented_income, 2),
            "total_net_income_rupees": round(total_net_income, 2)
        },
        "loan_details": {
            "tenure_years": 5,
            "eligibility_rupees": round(eligibility_rupees, 2),
            "eligibility_lakhs": round(eligibility_lakhs, 2),
            "status": status
        }
    }
