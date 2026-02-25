def analyze_banking(transactions, od_limit=0):
    total_credit = 0
    total_debit = 0
    cash_credit = 0
    bounce_count = 0
    emi_bounce = 0

    monthly_credit = {}

    for t in transactions:
        amount = float(t["amount"])
        desc = t["description"].lower()
        month = t["date"][:7]

        if t["type"] == "credit":
            total_credit += amount
            monthly_credit[month] = monthly_credit.get(month, 0) + amount
            if "cash" in desc:
                cash_credit += amount

        if t["type"] == "debit":
            total_debit += amount

        if "return" in desc or "bounce" in desc:
            bounce_count += 1

        if "emi" in desc and "return" in desc:
            emi_bounce += 1

    avg_monthly_credit = (
        total_credit / len(monthly_credit) if monthly_credit else 0
    )

    cash_ratio = (cash_credit / total_credit * 100) if total_credit else 0

    risk_score = 100

    if bounce_count > 3:
        risk_score -= 20
    if emi_bounce > 0:
        risk_score -= 20
    if cash_ratio > 50:
        risk_score -= 10
    if od_limit > 0:
        if total_debit > od_limit * 0.9:
            risk_score -= 15

    return {
        "total_credit": total_credit,
        "total_debit": total_debit,
        "avg_monthly_credit": avg_monthly_credit,
        "bounce_count": bounce_count,
        "emi_bounce": emi_bounce,
        "cash_ratio": round(cash_ratio, 2),
        "risk_score": risk_score,
        "monthly_credit": monthly_credit,
    }
