from utils.safe_math import safe_divide, default_zero

def analyze_banking(data: dict):

    total_credit = default_zero(data.get("total_credit"))
    total_debit = default_zero(data.get("total_debit"))
    months = default_zero(data.get("months"))

    avg_credit = safe_divide(total_credit, months)
    avg_debit = safe_divide(total_debit, months)

    net_surplus = avg_credit - avg_debit

    status = "Healthy" if net_surplus > 0 else "Risk"

    return {
        "average_monthly_credit": round(avg_credit, 2),
        "average_monthly_debit": round(avg_debit, 2),
        "net_monthly_surplus": round(net_surplus, 2),
        "status": status
    }
