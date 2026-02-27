from collections import defaultdict
from datetime import datetime


def analyze_banking(transactions):

    monthly_credit = defaultdict(float)
    monthly_debit = defaultdict(float)

    total_credit = 0.0
    total_debit = 0.0
    bounce_count = 0
    emi_bounce_count = 0
    fraud_flags = 0
    cash_credit_total = 0.0

    credit_list = []

    for t in transactions:

        credit = float(t.get("credit", 0))
        debit = float(t.get("debit", 0))
        desc = str(t.get("description", "")).lower()
        date_str = t.get("date")

        month_key = extract_month(date_str)

        total_credit += credit
        total_debit += debit

        if month_key:
            monthly_credit[month_key] += credit
            monthly_debit[month_key] += debit

        if "return" in desc or "bounce" in desc:
            bounce_count += 1
            if "emi" in desc:
                emi_bounce_count += 1

        if "cash" in desc:
            cash_credit_total += credit

        if credit > 5000000:
            fraud_flags += 1

        if credit > 0:
            credit_list.append(credit)

    months = max(1, len(monthly_credit))

    avg_monthly_credit = total_credit / months
    avg_monthly_debit = total_debit / months
    net_monthly_surplus = avg_monthly_credit - avg_monthly_debit

    cash_ratio = (cash_credit_total / total_credit * 100) if total_credit > 0 else 0

    credit_list.sort(reverse=True)

    concentration_ratio = (
        sum(credit_list[:5]) / total_credit * 100
        if total_credit > 0 else 0
    )

    hygiene_score = 100

    if net_monthly_surplus < 0:
        hygiene_score -= 30

    hygiene_score -= min(bounce_count * 5, 25)
    hygiene_score -= min(emi_bounce_count * 10, 20)

    if cash_ratio > 60:
        hygiene_score -= 10

    if concentration_ratio > 70:
        hygiene_score -= 10

    hygiene_score -= min(fraud_flags * 10, 20)

    hygiene_score = max(0, min(hygiene_score, 100))

    if hygiene_score >= 80:
        risk_grade, hygiene_status = "A", "Strong"
    elif hygiene_score >= 65:
        risk_grade, hygiene_status = "B", "Good"
    elif hygiene_score >= 50:
        risk_grade, hygiene_status = "C", "Moderate"
    else:
        risk_grade, hygiene_status = "D", "Weak"

    return {
        "summary": {
            "avg_monthly_credit": round(avg_monthly_credit, 2),
            "avg_monthly_debit": round(avg_monthly_debit, 2),
            "net_monthly_surplus": round(net_monthly_surplus, 2)
        },
        "bounce_count": bounce_count,
        "emi_bounce_count": emi_bounce_count,
        "cash_ratio_percent": round(cash_ratio, 2),
        "credit_concentration_percent": round(concentration_ratio, 2),
        "fraud_flags": fraud_flags,
        "hygiene_score": hygiene_score,
        "risk_grade": risk_grade,
        "hygiene_status": hygiene_status,
        "chart_data": {
            "monthly_trend": [
                {
                    "month": m,
                    "credit": round(monthly_credit[m], 2),
                    "debit": round(monthly_debit[m], 2)
                }
                for m in sorted(monthly_credit.keys())
            ]
        }
    }


def extract_month(date_str):
    try:
        if not date_str:
            return None

        try:
            dt = datetime.strptime(date_str, "%d/%m/%y")
        except:
            dt = datetime.strptime(date_str, "%Y-%m-%d")

        return dt.strftime("%Y-%m")

    except:
        return None
