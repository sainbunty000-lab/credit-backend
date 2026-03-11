from collections import defaultdict
from datetime import datetime
import re


# ======================================================
# SAFE NUMBER PARSER
# ======================================================

def safe_float(value):

    try:

        if value is None:
            return 0.0

        value = str(value)

        value = value.replace(",", "")
        value = value.replace("₹", "")
        value = value.strip()

        return float(value)

    except:
        return 0.0


# ======================================================
# MAIN BANKING ANALYSIS
# ======================================================

def analyze_banking(transactions):

    total_credit = 0
    total_debit = 0

    credit_txn = 0
    debit_txn = 0

    salary_income = 0
    upi_spend = 0
    emi_total = 0

    bounce = 0
    negative_balance = 0

    monthly_credit = defaultdict(float)
    monthly_debit = defaultdict(float)

    dates = []

    for txn in transactions:

        desc = str(txn.get("description", "")).lower()

        credit = safe_float(txn.get("credit"))
        debit = safe_float(txn.get("debit"))
        balance = safe_float(txn.get("balance"))

        date_value = txn.get("date")

        if date_value:
            dates.append(date_value)

        total_credit += credit
        total_debit += debit

        if credit > 0:
            credit_txn += 1

        if debit > 0:
            debit_txn += 1

        # ======================================================
        # INCOME DETECTION
        # ======================================================

        if "salary" in desc or "sal credit" in desc:
            salary_income += credit

        # ======================================================
        # EXPENSE DETECTION
        # ======================================================

        if "upi" in desc or "upi/" in desc:
            upi_spend += debit

        if "emi" in desc or "loan" in desc or "nach" in desc:
            emi_total += debit

        # ======================================================
        # BEHAVIOR FLAGS
        # ======================================================

        if "return" in desc or "bounce" in desc:
            bounce += 1

        if balance < 0:
            negative_balance += 1

        # ======================================================
        # MONTHLY TREND
        # ======================================================

        month = extract_month(date_value)

        if month:

            monthly_credit[month] += credit
            monthly_debit[month] += debit


    # ======================================================
    # SUMMARY METRICS
    # ======================================================

    net = total_credit - total_debit

    expense_ratio = (total_debit / total_credit * 100) if total_credit else 0

    salary_dependency = (
        salary_income / total_credit * 100
        if total_credit else 0
    )

    emi_ratio = (
        emi_total / salary_income * 100
        if salary_income else 0
    )

    # ======================================================
    # RISK SCORING
    # ======================================================

    score = 100

    if net < 0:
        score -= 30

    if expense_ratio > 100:
        score -= 20

    if emi_ratio > 50:
        score -= 20

    score -= bounce * 10
    score -= negative_balance * 10

    score = max(0, min(score, 100))


    # ======================================================
    # RISK GRADE
    # ======================================================

    grade = "A"
    status = "Strong"

    if score < 50:
        grade = "D"
        status = "Weak"

    elif score < 65:
        grade = "C"
        status = "Moderate"

    elif score < 80:
        grade = "B"
        status = "Good"


    # ======================================================
    # FINAL RESPONSE
    # ======================================================

    return {

        "statement_period": {
            "from": min(dates) if dates else None,
            "to": max(dates) if dates else None
        },

        "statement_summary": {
            "total_credit": round(total_credit, 2),
            "total_debit": round(total_debit, 2),
            "net_surplus": round(net, 2),
            "credit_transactions": credit_txn,
            "debit_transactions": debit_txn
        },

        "income_analysis": {
            "salary_income": round(salary_income, 2),
            "salary_dependency_percent": round(salary_dependency, 2)
        },

        "expense_analysis": {
            "upi_spends": round(upi_spend, 2),
            "emi_total": round(emi_total, 2),
            "expense_ratio_percent": round(expense_ratio, 2),
            "emi_ratio_percent": round(emi_ratio, 2)
        },

        "behavior_analysis": {
            "bounce_count": bounce,
            "negative_balance_count": negative_balance
        },

        "risk_summary": {
            "hygiene_score": score,
            "risk_grade": grade,
            "status": status
        },

        "chart_data": {
            "monthly_trend": [
                {
                    "month": m,
                    "credit": round(monthly_credit[m], 2),
                    "debit": round(monthly_debit[m], 2)
                }
                for m in sorted(
                    set(monthly_credit) | set(monthly_debit)
                )
            ]
        }
    }


# ======================================================
# MONTH EXTRACTION
# ======================================================

def extract_month(date):

    if not date:
        return None

    formats = [
        "%d/%m/%y",
        "%d/%m/%Y",
        "%d-%m-%y",
        "%d-%m-%Y"
    ]

    for fmt in formats:

        try:

            d = datetime.strptime(date, fmt)

            return d.strftime("%Y-%m")

        except:
            continue

    return None
