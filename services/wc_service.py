from utils.safe_math import default_zero

def calculate_wc(data: dict):

    ca = default_zero(data.get("current_assets"))
    cl = default_zero(data.get("current_liabilities"))
    sales = default_zero(data.get("annual_sales"))

    nwc = ca - cl
    nwc_eligible = (0.75 * ca) - cl
    turnover_eligible = 0.20 * sales

    if nwc_eligible < 0:
        nwc_eligible = 0

    if turnover_eligible < 0:
        turnover_eligible = 0

    status = "Eligible" if max(nwc_eligible, turnover_eligible) > 0 else "Not Eligible"

    return {
        "nwc": round(nwc, 2),
        "nwc_eligible": round(nwc_eligible, 2),
        "turnover_eligible": round(turnover_eligible, 2),
        "status": status
    }
