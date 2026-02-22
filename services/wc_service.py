from utils.safe_math import safe_subtract, safe_divide

def calculate_wc_eligibility(current_assets, current_liabilities, annual_sales):
    ca = float(current_assets or 0)
    cl = float(current_liabilities or 0)
    sales = float(annual_sales or 0)

    # NWC = CA - CL
    nwc = safe_subtract(ca, cl)
    
    # NWC Method: 0.75 * CA - CL
    nwc_eligible = safe_subtract((0.75 * ca), cl)
    
    # Turnover Method: 0.20 * Sales
    turnover_eligible = 0.20 * sales
    
    status = "Eligible" if (nwc_eligible > 0 or turnover_eligible > 0) else "Not Eligible"

    return {
        "nwc": round(nwc, 2),
        "nwc_eligible": round(nwc_eligible, 2),
        "turnover_eligible": round(turnover_eligible, 2),
        "status": status
    }
