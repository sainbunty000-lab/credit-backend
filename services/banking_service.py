from collections import defaultdict
from datetime import datetime
import statistics


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(v):

    try:
        return float(v)
    except:
        return 0.0


# =========================================================
# MAIN BANKING ANALYZER
# =========================================================

def analyze_banking(transactions):

    if not transactions:
        return empty_response()

    total_credit = 0
    total_debit = 0

    credit_txn = 0
    debit_txn = 0

    salary_income = 0
    emi_total = 0
    upi_spend = 0
    cash_deposit = 0

    bounce = 0
    negative_balance = 0

    monthly_credit = defaultdict(float)
    monthly_debit = defaultdict(float)
    balances = []

    dates = []

    # =====================================================
    # LOOP TRANSACTIONS
    # =====================================================

    for txn in transactions:

        desc = str(txn.get("description", "")).lower()

        credit = safe_float(txn.get("credit"))
        debit = safe_float(txn.get("debit"))
        balance = safe_float(txn.get("balance"))

        date_value = txn.get("date")

        month = extract_month(date_value)

        if month:
            monthly_credit[month] += credit
            monthly_debit[month] += debit

        if date_value:
            dates.append(date_value)

        balances.append(balance)

        total_credit += credit
        total_debit += debit

        if credit > 0:
            credit_txn += 1

        if debit > 0:
            debit_txn += 1

        # --------------------------------------------------
        # INCOME CLASSIFICATION
        # --------------------------------------------------

        if "salary" in desc:
            salary_income += credit

        if "cash deposit" in desc:
            cash_deposit += credit

        # --------------------------------------------------
        # EXPENSE CLASSIFICATION
        # --------------------------------------------------

        if "emi" in desc or "loan" in desc:
            emi_total += debit

        if "upi" in desc or "gpay" in desc or "phonepe" in desc:
            upi_spend += debit

        # --------------------------------------------------
        # BEHAVIOR FLAGS
        # --------------------------------------------------

        if "return" in desc or "bounce" in desc:
            bounce += 1

        if balance < 0:
            negative_balance += 1

    # =====================================================
    # SUMMARY METRICS
    # =====================================================

    net = total_credit - total_debit

    expense_ratio = safe_divide(total_debit, total_credit) * 100

    salary_dependency = safe_divide(salary_income, total_credit) * 100

    avg_balance = statistics.mean(balances) if balances else 0

    median_balance = statistics.median(balances) if balances else 0

    # =====================================================
    # CASH FLOW STABILITY
    # =====================================================

    monthly_net = []

    for m in sorted(set(monthly_credit) | set(monthly_debit)):

        net_m = monthly_credit[m] - monthly_debit[m]

        monthly_net.append(net_m)

    cashflow_stability = 0

    if len(monthly_net) > 1:

        variance = statistics.pvariance(monthly_net)

        if variance < 100000:
            cashflow_stability = 90

        elif variance < 500000:
            cashflow_stability = 70

        else:
            cashflow_stability = 50

    # =====================================================
    # RISK SCORING
    # =====================================================

    score = 100

    if net < 0:
        score -= 25

    if expense_ratio > 90:
        score -= 15

    score -= bounce * 10
    score -= negative_balance * 10

    if emi_total > salary_income * 0.5:
        score -= 15

    score = max(0, min(score, 100))

    # =====================================================
    # RISK GRADE
    # =====================================================

    if score >= 80:
        grade = "A"
        status = "Strong"

    elif score >= 65:
        grade = "B"
        status = "Good"

    elif score >= 50:
        grade = "C"
        status = "Moderate"

    else:
        grade = "D"
        status = "Weak"

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

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
            "debit_transactions": debit_txn,

            "average_balance": round(avg_balance, 2),
            "median_balance": round(median_balance, 2)
        },

        "income_analysis": {

            "salary_income": round(salary_income, 2),

            "salary_dependency_percent": round(salary_dependency, 2),

            "cash_deposit": round(cash_deposit, 2)
        },

        "expense_analysis": {

            "emi_total": round(emi_total, 2),

            "upi_spends": round(upi_spend, 2),

            "expense_ratio_percent": round(expense_ratio, 2)
        },

        "behavior_analysis": {

            "bounce_count": bounce,

            "negative_balance_count": negative_balance,

            "cashflow_stability_score": cashflow_stability
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

                for m in sorted(set(monthly_credit) | set(monthly_debit))
            ]
        }
    }


# =========================================================
# DATE PARSER
# =========================================================

def extract_month(date):

    try:

        d = datetime.strptime(date, "%d/%m/%y")

        return d.strftime("%Y-%m")

    except:

        try:
            d = datetime.strptime(date, "%d/%m/%Y")

            return d.strftime("%Y-%m")

        except:
            return None


# =========================================================
# SAFE DIVIDE
# =========================================================

def safe_divide(a, b):

    try:
        return a / b if b else 0
    except:
        return 0


# =========================================================
# EMPTY RESPONSE
# =========================================================

def empty_response():

    return {

        "statement_summary": {},
        "income_analysis": {},
        "expense_analysis": {},
        "behavior_analysis": {},
        "risk_summary": {},
        "chart_data": {}
    }
