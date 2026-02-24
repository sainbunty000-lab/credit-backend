from collections import defaultdict
from datetime import datetime
from utils.safe_math import default_zero


def analyze_banking(transactions, months_count=3):

    # ===============================
    # PREPARE STRUCTURES
    # ===============================
    account_summary = defaultdict(lambda: {"credit": 0.0, "debit": 0.0})
    monthly_breakdown = defaultdict(lambda: {"credit": 0.0, "debit": 0.0})

    total_credit = 0.0
    total_debit = 0.0
    bounce_count = 0
    fraud_flags = 0

    # ===============================
    # PROCESS TRANSACTIONS
    # ===============================
    for t in transactions:

        credit = default_zero(t.get("credit"))
        debit = default_zero(t.get("debit"))
        desc = str(t.get("desc", "")).lower()
        account = t.get("account", "Unknown")
        date_str = t.get("date")

        total_credit += credit
        total_debit += debit

        # Account summary
        account_summary[account]["credit"] += credit
        account_summary[account]["debit"] += debit

        # Monthly grouping
        month_key = extract_month(date_str)
        if month_key:
            monthly_breakdown[month_key]["credit"] += credit
            monthly_breakdown[month_key]["debit"] += debit

        # Bounce detection
        if "return" in desc or "bounce" in desc:
            bounce_count += 1

        # Simple fraud pattern detection
        if credit > 1000000:  # large abnormal credit
            fraud_flags += 1

    # ===============================
    # CONSOLIDATED METRICS
    # ===============================
    months_count = max(1, months_count)

    avg_monthly_credit = total_credit / months_count
    avg_monthly_debit = total_debit / months_count
    net_monthly_surplus = avg_monthly_credit - avg_monthly_debit

    hygiene_score = calculate_hygiene_score(
        net_monthly_surplus,
        bounce_count,
        fraud_flags
    )

    hygiene_status = classify_hygiene(hygiene_score)

    return {
        "consolidated": {
            "avg_monthly_credit": round(avg_monthly_credit, 2),
            "avg_monthly_debit": round(avg_monthly_debit, 2),
            "net_monthly_surplus": round(net_monthly_surplus, 2),
        },
        "account_summary": dict(account_summary),
        "monthly_breakdown": dict(monthly_breakdown),
        "hygiene_score": hygiene_score,
        "hygiene_status": hygiene_status,
        "bounce_count": bounce_count,
        "fraud_flags": fraud_flags,
    }


# =============================================
# HYGIENE SCORE ENGINE
# =============================================
def calculate_hygiene_score(surplus, bounce_count, fraud_flags):

    score = 100

    # Negative surplus penalty
    if surplus < 0:
        score -= 40

    # Bounce penalty
    score -= bounce_count * 5

    # Fraud penalty
    score -= fraud_flags * 10

    return max(0, min(score, 100))


def classify_hygiene(score):

    if score >= 80:
        return "Strong"
    elif score >= 60:
        return "Moderate"
    else:
        return "Weak"


# =============================================
# MONTH EXTRACTOR
# =============================================
def extract_month(date_str):
    try:
        if not date_str:
            return None

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m")
    except Exception:
        return None
