from collections import defaultdict
from datetime import datetime


# =================================
# MAIN ANALYSIS FUNCTION
# =================================

def analyze_banking(transactions):

    total_credit = 0.0
    total_debit = 0.0
    credit_txn_count = 0
    debit_txn_count = 0

    salary_credit_total = 0.0
    mf_redemption_total = 0.0
    loan_disbursal_total = 0.0
    emi_debit_total = 0.0
    sip_investment_total = 0.0
    upi_spend_total = 0.0
    bounce_count = 0
    negative_balance_count = 0
    cash_credit_total = 0.0

    monthly_credit = defaultdict(float)
    monthly_debit = defaultdict(float)

    for txn in transactions:

        date_str = txn.get("date")
        description = str(txn.get("description", "")).lower()
        credit = float(txn.get("credit", 0))
        debit = float(txn.get("debit", 0))
        balance = float(txn.get("balance", 0))

        # -----------------------------
        # Totals
        # -----------------------------
        total_credit += credit
        total_debit += debit

        if credit > 0:
            credit_txn_count += 1

        if debit > 0:
            debit_txn_count += 1

        # -----------------------------
        # Monthly grouping
        # -----------------------------
        month_key = extract_month(date_str)
        if month_key:
            monthly_credit[month_key] += credit
            monthly_debit[month_key] += debit

        # -----------------------------
        # Negative balance detection
        # -----------------------------
        if balance < 0:
            negative_balance_count += 1

        # -----------------------------
        # Income Detection
        # -----------------------------
        if "salary" in description:
            salary_credit_total += credit

        if credit > 0 and (
            "mutual fund" in description
            or "mf redemption" in description
            or "redemption" in description
        ):
            mf_redemption_total += credit

        if credit > 0 and "loan" in description:
            loan_disbursal_total += credit

        if "cash" in description and credit > 0:
            cash_credit_total += credit

        # -----------------------------
        # Expense Detection
        # -----------------------------
        if debit > 0 and (
            "emi" in description
            or "finance" in description
            or "capital" in description
            or "clix" in description
            or "respo" in description
        ):
            emi_debit_total += debit

        if debit > 0 and (
            "o-mf" in description
            or "sip" in description
        ):
            sip_investment_total += debit

        if debit > 0 and "upi" in description:
            upi_spend_total += debit

        # -----------------------------
        # Bounce detection
        # -----------------------------
        if "return" in description or "bounce" in description:
            bounce_count += 1

    # =========================================
    # METRICS
    # =========================================

    net_surplus = total_credit - total_debit

    salary_dependency = (
        (salary_credit_total / total_credit) * 100
        if total_credit > 0 else 0
    )

    expense_ratio = (
        (total_debit / total_credit) * 100
        if total_credit > 0 else 0
    )

    emi_ratio = (
        (emi_debit_total / salary_credit_total) * 100
        if salary_credit_total > 0 else 0
    )

    cash_ratio = (
        (cash_credit_total / total_credit) * 100
        if total_credit > 0 else 0
    )

    # =========================================
    # HYGIENE SCORE ENGINE (Improved)
    # =========================================

    score = 100

    if net_surplus < 1000:
        score -= 25

    if emi_ratio > 50:
        score -= 20

    if expense_ratio > 95:
        score -= 10

    score -= bounce_count * 7
    score -= negative_balance_count * 10

    if salary_dependency > 80:
        score -= 10

    score = max(0, min(score, 100))

    if score >= 80:
        risk_grade = "A"
        status = "Strong"
    elif score >= 65:
        risk_grade = "B"
        status = "Good"
    elif score >= 50:
        risk_grade = "C"
        status = "Moderate"
    else:
        risk_grade = "D"
        status = "Weak"

    # =========================================
    # RETURN STRUCTURED RESPONSE
    # =========================================

    return {

        "statement_summary": {
            "total_credit": round(total_credit, 2),
            "total_debit": round(total_debit, 2),
            "net_surplus": round(net_surplus, 2),
            "credit_transactions": credit_txn_count,
            "debit_transactions": debit_txn_count
        },

        "income_analysis": {
            "salary_income": round(salary_credit_total, 2),
            "mutual_fund_redemptions": round(mf_redemption_total, 2),
            "loan_disbursals": round(loan_disbursal_total, 2),
            "salary_dependency_percent": round(salary_dependency, 2)
        },

        "expense_analysis": {
            "emi_total": round(emi_debit_total, 2),
            "sip_investments": round(sip_investment_total, 2),
            "upi_spends": round(upi_spend_total, 2),
            "expense_ratio_percent": round(expense_ratio, 2),
            "emi_ratio_percent": round(emi_ratio, 2)
        },

        "behavior_analysis": {
            "negative_balance_count": negative_balance_count,
            "bounce_count": bounce_count,
            "cash_ratio_percent": round(cash_ratio, 2)
        },

        "risk_summary": {
            "hygiene_score": score,
            "risk_grade": risk_grade,
            "status": status
        },

        "chart_data": {
            "monthly_trend": [
                {
                    "month": m,
                    "credit": round(monthly_credit[m], 2),
                    "debit": round(monthly_debit[m], 2)
                }
                for m in sorted(set(list(monthly_credit.keys()) + list(monthly_debit.keys())))
            ]
        }
    }


# =================================
# HELPER
# =================================

def extract_month(date_str):
    try:
        dt = datetime.strptime(date_str, "%d/%m/%y")
        return dt.strftime("%Y-%m")
    except:
        return None
