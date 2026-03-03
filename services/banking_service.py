from collections import defaultdict
from datetime import datetime


# ================================
# MAIN ANALYSIS FUNCTION
# ================================

def analyze_banking(transactions):

    total_credit = 0.0
    total_debit = 0.0
    salary_credit_total = 0.0
    mf_redemption_total = 0.0
    loan_disbursal_total = 0.0
    bounce_count = 0
    negative_balance_count = 0
    emi_debit_total = 0.0
    cash_credit_total = 0.0

    monthly_credit = defaultdict(float)
    monthly_debit = defaultdict(float)

    running_balance = 0.0
    salary_day_outflows = []

    for txn in transactions:
        date_str = txn.get("date")
        description = str(txn.get("description", "")).lower()
        credit = float(txn.get("credit", 0) or 0)
        debit = float(txn.get("debit", 0) or 0)
        balance = txn.get("balance")

        total_credit += credit
        total_debit += debit

        # Monthly grouping
        month_key = extract_month(date_str)
        if month_key:
            monthly_credit[month_key] += credit
            monthly_debit[month_key] += debit

        # Running balance detection
        if balance is not None:
            running_balance = float(balance)
        else:
            running_balance = running_balance + credit - debit

        if running_balance < 0:
            negative_balance_count += 1

        # Salary detection
        if "salary" in description:
            salary_credit_total += credit
            salary_day = date_str

        # Mutual fund detection
        if "mf" in description or "mutual" in description:
            mf_redemption_total += credit

        # Loan disbursal detection
        if "loan" in description or "disbursal" in description:
            loan_disbursal_total += credit

        # EMI detection
        if "emi" in description or "finance" in description:
            emi_debit_total += debit

        # Bounce detection
        if "return" in description or "bounce" in description:
            bounce_count += 1

        # Cash detection
        if "cash" in description:
            cash_credit_total += credit

    # ================================
    # SUMMARY CALCULATIONS
    # ================================

    months = max(1, len(monthly_credit))

    avg_monthly_credit = total_credit / months
    avg_monthly_debit = total_debit / months
    net_surplus = avg_monthly_credit - avg_monthly_debit

    salary_dependency = (
        (salary_credit_total / total_credit) * 100
        if total_credit > 0 else 0
    )

    expense_ratio = (
        (total_debit / total_credit) * 100
        if total_credit > 0 else 0
    )

    cash_ratio = (
        (cash_credit_total / total_credit) * 100
        if total_credit > 0 else 0
    )

    # ================================
    # HYGIENE SCORE LOGIC
    # ================================

    score = 100

    if net_surplus < 1000:
        score -= 30

    score -= bounce_count * 5
    score -= negative_balance_count * 10

    if salary_dependency > 70:
        score -= 10

    if expense_ratio > 90:
        score -= 10

    score = max(0, min(score, 100))

    # Risk Grade Mapping
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

    # ================================
    # STRUCTURED RESPONSE
    # ================================

    return {

        "statement_summary": {
            "total_credit": round(total_credit, 2),
            "total_debit": round(total_debit, 2),
            "net_surplus": round(net_surplus, 2),
            "credit_transactions": count_credit_txns(transactions),
            "debit_transactions": count_debit_txns(transactions)
        },

        "income_analysis": {
            "salary_income": round(salary_credit_total, 2),
            "mutual_fund_redemptions": round(mf_redemption_total, 2),
            "loan_disbursals": round(loan_disbursal_total, 2),
            "salary_dependency_percent": round(salary_dependency, 2)
        },

        "expense_analysis": {
            "emi_total": round(emi_debit_total, 2),
            "expense_ratio_percent": round(expense_ratio, 2),
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
                for m in sorted(monthly_credit.keys())
            ]
        }
    }


# ================================
# HELPER FUNCTIONS
# ================================

def extract_month(date_str):
    try:
        dt = datetime.strptime(date_str, "%d/%m/%y")
        return dt.strftime("%Y-%m")
    except:
        return None


def count_credit_txns(transactions):
    return sum(1 for t in transactions if float(t.get("credit", 0)) > 0)


def count_debit_txns(transactions):
    return sum(1 for t in transactions if float(t.get("debit", 0)) > 0)
