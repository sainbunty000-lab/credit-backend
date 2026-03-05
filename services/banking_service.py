from collections import defaultdict
from datetime import datetime


def analyze_banking(transactions):

    total_credit = 0
    total_debit = 0

    credit_txn = 0
    debit_txn = 0

    salary_income = 0
    upi_spend = 0
    bounce = 0
    negative_balance = 0

    monthly_credit = defaultdict(float)
    monthly_debit = defaultdict(float)

    dates = []

    for txn in transactions:

        desc = str(txn["description"]).lower()

        credit = float(txn["credit"])
        debit = float(txn["debit"])
        balance = float(txn["balance"])

        dates.append(txn["date"])

        total_credit += credit
        total_debit += debit

        if credit > 0:
            credit_txn += 1

        if debit > 0:
            debit_txn += 1

        if "salary" in desc:
            salary_income += credit

        if "upi" in desc:
            upi_spend += debit

        if "return" in desc or "bounce" in desc:
            bounce += 1

        if balance < 0:
            negative_balance += 1

        month = extract_month(txn["date"])

        if month:
            monthly_credit[month] += credit
            monthly_debit[month] += debit


    net = total_credit - total_debit

    expense_ratio = (total_debit / total_credit * 100) if total_credit else 0
    salary_dependency = (salary_income / total_credit * 100) if total_credit else 0

    score = 100

    if net < 0:
        score -= 30

    if expense_ratio > 100:
        score -= 20

    score -= bounce * 10
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

        "statement_period": {
            "from": min(dates) if dates else None,
            "to": max(dates) if dates else None
        },

        "statement_summary": {
            "total_credit": round(total_credit,2),
            "total_debit": round(total_debit,2),
            "net_surplus": round(net,2),
            "credit_transactions": credit_txn,
            "debit_transactions": debit_txn
        },

        "income_analysis": {
            "salary_income": round(salary_income,2),
            "salary_dependency_percent": round(salary_dependency,2)
        },

        "expense_analysis": {
            "upi_spends": round(upi_spend,2),
            "expense_ratio_percent": round(expense_ratio,2)
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


def extract_month(date):

    try:
        d = datetime.strptime(date,"%d/%m/%y")
        return d.strftime("%Y-%m")
    except:
        return None
