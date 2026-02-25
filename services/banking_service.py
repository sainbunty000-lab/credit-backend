from collections import defaultdict
from datetime import datetime
from utils.safe_math import default_zero


def analyze_banking(transactions):

    # ===============================
    # DATA STRUCTURES
    # ===============================
    monthly_credit = defaultdict(float)
    monthly_debit = defaultdict(float)

    total_credit = 0.0
    total_debit = 0.0

    bounce_count = 0
    emi_bounce_count = 0
    fraud_flags = 0
    cash_credit_total = 0.0

    credit_list = []

    # ===============================
    # PROCESS TRANSACTIONS
    # ===============================
    for t in transactions:

        credit = default_zero(t.get("credit"))
        debit = default_zero(t.get("debit"))
        desc = str(t.get("desc", "")).lower()
        date_str = t.get("date")

        month_key = extract_month(date_str)

        total_credit += credit
        total_debit += debit

        if month_key:
            monthly_credit[month_key] += credit
            monthly_debit[month_key] += debit

        # Bounce detection
        if "return" in desc or "bounce" in desc:
            bounce_count += 1

        # EMI detection
        if "emi" in desc:
            if "return" in desc or "bounce" in desc:
                emi_bounce_count += 1

        # Cash deposit detection
        if "cash" in desc:
            cash_credit_total += credit

        # Fraud detection (abnormally large credit)
        if credit > 5000000:
            fraud_flags += 1

        if credit > 0:
            credit_list.append(credit)

    # ===============================
    # MONTHLY METRICS
    # ===============================
    months = max(1, len(monthly_credit))

    avg_monthly_credit = total_credit / months
    avg_monthly_debit = total_debit / months
    net_monthly_surplus = avg_monthly_credit - avg_monthly_debit

    # ===============================
    # CASH RATIO
    # ===============================
    cash_ratio = (
        (cash_credit_total / total_credit) * 100
        if total_credit > 0 else 0
    )

    # ===============================
    # CREDIT CONCENTRATION
    # ===============================
    credit_list.sort(reverse=True)
    top_5_sum = sum(credit_list[:5])
    concentration_ratio = (
        (top_5_sum / total_credit) * 100
        if total_credit > 0 else 0
    )

    # ===============================
    # HYGIENE SCORE CALCULATION
    # ===============================
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

    # ===============================
    # RISK GRADE
    # ===============================
    if hygiene_score >= 80:
        risk_grade = "A"
        hygiene_status = "Strong"
    elif hygiene_score >= 65:
        risk_grade = "B"
        hygiene_status = "Good"
    elif hygiene_score >= 50:
        risk_grade = "C"
        hygiene_status = "Moderate"
    else:
        risk_grade = "D"
        hygiene_status = "Weak"

    # ===============================
    # CHART READY STRUCTURE
    # ===============================
    chart_data = {
        "monthly_trend": [
            {
                "month": month,
                "credit": round(monthly_credit[month], 2),
                "debit": round(monthly_debit[month], 2)
            }
            for month in sorted(monthly_credit.keys())
        ],
        "ratios": {
            "cash_ratio": round(cash_ratio, 2),
            "concentration_ratio": round(concentration_ratio, 2)
        }
    }

    # ===============================
    # FINAL RESPONSE
    # ===============================
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
        "chart_data": chart_data
    }


# ===============================
# MONTH EXTRACTOR
# ===============================
def extract_month(date_str):
    try:
        if not date_str:
            return None
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m")
    except Exception:
        return None
