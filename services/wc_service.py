from utils.safe_math import safe_subtract, default_zero

def calculate_wc_logic(ca, cl, sales):
    ca, cl, sales = default_zero(ca), default_zero(cl), default_zero(sales)
    
    # Section 2: Method 1 - NWC
    nwc = safe_subtract(ca, cl)
    nwc_limit = safe_subtract((0.75 * ca), cl)
    
    # Section 2: Method 2 - Turnover
    turnover_limit = 0.20 * sales
    
    is_eligible = nwc_limit > 0 or turnover_limit > 0
    
    return {
        "nwc": round(nwc, 2),
        "nwc_eligible": round(nwc_limit, 2),
        "turnover_eligible": round(turnover_limit, 2),
        "status": "Eligible" if is_eligible else "Not Eligible",
        "reason": "" if is_eligible else "Insufficient financial data or negative working capital"
    }
