from utils.safe_math import default_zero

def calculate_wc(data: dict):

    ca = default_zero(data.get("current_assets"))
    cl = default_zero(data.get("current_liabilities"))
    sales = default_zero(data.get("annual_sales"))

    nwc = ca - cl
    nwc_eligible = (0.75 * ca) - cl
    turnover_eligible = 0.20 * sales

    nwc_eligible = max(nwc_eligible, 0)
    turnover_eligible = max(turnover_eligible, 0)

    final = max(nwc_eligible, turnover_eligible)

    return {
        "nwc": round(nwc, 2),
        "nwc_eligible": round(nwc_eligible, 2),
        "turnover_eligible": round(turnover_eligible, 2),
        "final_eligible": round(final, 2),
        "status": "Eligible" if final > 0 else "Not Eligible"
    }
