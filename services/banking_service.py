from collections import defaultdict
from datetime import datetime
import statistics

# ==============================
# MAIN ENTRY
# ==============================

def analyze_banking(transactions):

    monthly_credit = defaultdict(float)
    monthly_debit = defaultdict(float)
    credit_list = []
    total_credit = 0
    total_debit = 0

    bounce_count = 0
    emi_total = 0
    cash_credit_total = 0
    fraud_flags = 0

    # ==============================
    # LOOP THROUGH TRANSACTIONS
    # ==============================

    for t in transactions:

        credit = safe_float(t.get("credit"))
        debit = safe_float(t.get("debit"))
        desc = str(t.get("description", "")).lower()
        month = extract_month(t.get("date"))

        # Sanity filter (prevent 12-digit reference errors)
        if credit > 10_000_000:
            credit = 0

        total_credit += credit
        total_debit += debit

        if month:
            monthly_credit[month] += credit
            monthly_debit[month] += debit

        if credit > 0:
            credit_list.append(credit)

        # EMI detection
        if "emi" in desc:
            emi_total += debit

        # Bounce detection
        if "bounce" in desc or "return" in desc:
            bounce_count += 1

        # Cash credit detection
        if "cash" in desc:
            cash_credit_total += credit

        # Suspicious large credit
        if credit > 5_000_000:
            fraud_flags += 1

    # ==============================
    # BASIC CALCULATIONS
    # ==============================

    months = max(1, len(monthly_credit))
    avg_monthly_credit = total_credit / months
    avg_monthly_debit = total_debit / months
    net_surplus = avg_monthly_credit - avg_monthly_debit

    credit_values = list(monthly_credit.values())
    income_variance = statistics.stdev(credit_values) if len(credit_values) > 1 else 0
    income_stability_percent = (income_variance / avg_monthly_credit * 100) if avg_monthly_credit > 0 else 0

    expense_ratio = (avg_monthly_debit / avg_monthly_credit * 100) if avg_monthly_credit > 0 else 0
    emi_ratio = (emi_total / total_credit * 100) if total_credit > 0 else 0
    cash_ratio = (cash_credit_total / total_credit * 100) if total_credit > 0 else 0

    credit_list.sort(reverse=True)
    concentration_ratio = (sum(credit_list[:5]) / total_credit * 100) if total_credit > 0 else 0

    # ==============================
    # MODULE 1: INCOME SCORE
    # ==============================

    income_score = 100
    if income_stability_percent > 40:
        income_score -= 30
    elif income_stability_percent > 25:
        income_score -= 15

    # ==============================
    # MODULE 2: EXPENSE SCORE
    # ==============================

    expense_score = 100
    if expense_ratio > 80:
        expense_score -= 30
    elif expense_ratio > 65:
        expense_score -= 15

    if emi_ratio > 50:
        expense_score -= 20

    # ==============================
    # MODULE 3: BEHAVIOR SCORE
    # ==============================

    behavior_score = 100
    behavior_score -= min(bounce_count * 10, 40)

    # ==============================
    # MODULE 4: FRAUD SCORE
    # ==============================

    fraud_score = 100
    if concentration_ratio > 70:
        fraud_score -= 20

    fraud_score -= min(fraud_flags * 10, 30)

    # ==============================
    # FINAL WEIGHTED SCORE
    # ==============================

    final_score = (
        income_score * 0.30 +
        expense_score * 0.25 +
        behavior_score * 0.20 +
        fraud_score * 0.15 +
        100 * 0.10
    )

    final_score = round(max(0, min(final_score, 100)), 2)

    if final_score >= 80:
        risk_grade = "A"
        recommendation = "Strong Approval"
    elif final_score >= 65:
        risk_grade = "B"
        recommendation = "Approve with Monitoring"
    elif final_score >= 50:
        risk_grade = "C"
        recommendation = "High Risk – Review Required"
    else:
        risk_grade = "D"
        recommendation = "Reject"

    return {
        "income_analysis": {
            "avg_monthly_credit": round(avg_monthly_credit, 2),
            "income_stability_percent": round(income_stability_percent, 2),
            "net_monthly_surplus": round(net_surplus, 2)
        },
        "expense_analysis": {
            "avg_monthly_debit": round(avg_monthly_debit, 2),
            "expense_ratio_percent": round(expense_ratio, 2),
            "emi_ratio_percent": round(emi_ratio, 2)
        },
        "behavior_analysis": {
            "bounce_count": bounce_count,
            "cash_ratio_percent": round(cash_ratio, 2)
        },
        "fraud_analysis": {
            "credit_concentration_percent": round(concentration_ratio, 2),
            "fraud_flags": fraud_flags
        },
        "risk_summary": {
            "final_score": final_score,
            "risk_grade": risk_grade,
            "recommendation": recommendation
        },
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


# ==============================
# HELPERS
# ==============================

def extract_month(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m")
    except:
        try:
            dt = datetime.strptime(date_str, "%d/%m/%y")
            return dt.strftime("%Y-%m")
        except:
            return None


def safe_float(value):
    try:
        return float(value)
    except:
        return 0
