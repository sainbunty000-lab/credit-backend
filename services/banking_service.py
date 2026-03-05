from collections import defaultdict
from datetime import datetime


def analyze_banking(transactions):

    total_credit = 0
    total_debit = 0

    credit_txn = 0
    debit_txn = 0

    salary_income = 0
    mf_redemption = 0
    loan_disbursal = 0

    emi_total = 0
    sip_total = 0
    upi_total = 0

    bounce = 0
    negative_balance = 0
    cash_credit = 0

    monthly_credit = defaultdict(float)
    monthly_debit = defaultdict(float)

    for txn in transactions:

        desc = str(txn["description"]).lower()
        credit = safe(txn["credit"])
        debit = safe(txn["debit"])
        balance = safe(txn["balance"])

        total_credit += credit
        total_debit += debit

        if credit > 0:
            credit_txn += 1

        if debit > 0:
            debit_txn += 1

        month = extract_month(txn["date"])

        if month:
            monthly_credit[month] += credit
            monthly_debit[month] += debit

        if balance < 0:
            negative_balance += 1

        if "salary" in desc:
            salary_income += credit

        if "redemption" in desc:
            mf_redemption += credit

        if "loan" in desc:
            loan_disbursal += credit

        if "cash" in desc:
            cash_credit += credit

        if "emi" in desc or "finance" in desc:
            emi_total += debit

        if "o-mf" in desc or "sip" in desc:
            sip_total += debit

        if "upi" in desc:
            upi_total += debit

        if "return" in desc or "bounce" in desc:
            bounce += 1

    net = total_credit - total_debit

    salary_dependency = percent(salary_income, total_credit)
    expense_ratio = percent(total_debit, total_credit)
    emi_ratio = percent(emi_total, salary_income)
    cash_ratio = percent(cash_credit, total_credit)

    score = 100

    if net < 1000:
        score -= 25

    if emi_ratio > 50:
        score -= 20

    if expense_ratio > 95:
        score -= 10

    score -= bounce * 7
    score -= negative_balance * 10

    score = max(0, min(score, 100))

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

    return {

        "statement_summary": {
            "total_credit": round(total_credit,2),
            "total_debit": round(total_debit,2),
            "net_surplus": round(net,2),
            "credit_transactions": credit_txn,
            "debit_transactions": debit_txn
        },

        "income_analysis": {
            "salary_income": round(salary_income,2),
            "mutual_fund_redemptions": round(mf_redemption,2),
            "loan_disbursals": round(loan_disbursal,2),
            "salary_dependency_percent": round(salary_dependency,2)
        },

        "expense_analysis": {
            "emi_total": round(emi_total,2),
            "sip_investments": round(sip_total,2),
            "upi_spends": round(upi_total,2),
            "expense_ratio_percent": round(expense_ratio,2),
            "emi_ratio_percent": round(emi_ratio,2)
        },

        "behavior_analysis": {
            "negative_balance_count": negative_balance,
            "bounce_count": bounce,
            "cash_ratio_percent": round(cash_ratio,2)
        },

        "risk_summary": {
            "hygiene_score": score,
            "risk_grade": grade,
            "status": status
        },

        "chart_data": {
            "monthly_trend":[
                {
                    "month":m,
                    "credit":round(monthly_credit[m],2),
                    "debit":round(monthly_debit[m],2)
                }
                for m in sorted(set(monthly_credit)|set(monthly_debit))
            ]
        }
    }


def safe(v):
    try:
        return float(v)
    except:
        return 0


def percent(a,b):
    return (a/b*100) if b>0 else 0


def extract_month(d):
    try:
        dt=datetime.strptime(d,"%d/%m/%y")
        return dt.strftime("%Y-%m")
    except:
        return None
