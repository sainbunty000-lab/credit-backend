from datetime import datetime
from services.banking_service import analyze_banking


# =====================================================
# MASTER ENTRY
# =====================================================

def analyze_transactions(transactions):

    if not transactions or not isinstance(transactions, list):
        return empty_response()

    # -------------------------------------
    # Normalize transactions
    # -------------------------------------
    cleaned = normalize_transactions(transactions)

    if not cleaned:
        return empty_response()

    # -------------------------------------
    # Sort transactions safely
    # -------------------------------------
    cleaned.sort(key=lambda x: parse_date_safe(x.get("date")))

    # -------------------------------------
    # Core banking analysis
    # -------------------------------------
    banking_result = analyze_banking(cleaned)

    # -------------------------------------
    # Add derived indicators
    # -------------------------------------
    enriched = enrich_with_indicators(banking_result)

    return enriched


# =====================================================
# NORMALIZATION
# =====================================================

def normalize_transactions(transactions):

    normalized = []

    for txn in transactions:

        try:

            normalized.append({

                "date": str(txn.get("date", "")).strip(),

                "description": str(
                    txn.get("description", "")
                ).strip(),

                "credit": normalize_number(txn.get("credit")),

                "debit": normalize_number(txn.get("debit")),

                "balance": normalize_number(txn.get("balance"))

            })

        except:
            continue

    return normalized


# =====================================================
# NUMBER NORMALIZATION
# =====================================================

def normalize_number(value):

    try:

        if value is None:
            return 0.0

        value = str(value)

        value = value.replace(",", "")
        value = value.replace("₹", "")

        return float(value)

    except:
        return 0.0


# =====================================================
# DERIVED FINANCIAL INDICATORS
# =====================================================

def enrich_with_indicators(result):

    summary = result.get("statement_summary", {})
    income = result.get("income_analysis", {})
    expense = result.get("expense_analysis", {})
    behavior = result.get("behavior_analysis", {})

    salary = normalize_number(income.get("salary_income", 0))
    emi = normalize_number(expense.get("emi_total", 0))
    net = normalize_number(summary.get("net_surplus", 0))

    # -------------------------------------
    # Financial Strength Index (FSI)
    # -------------------------------------

    fsi = 0

    # Savings behaviour
    if salary > 0:

        savings_ratio = (net / salary) * 100

        if savings_ratio > 20:
            fsi += 30
        elif savings_ratio > 10:
            fsi += 20
        elif savings_ratio > 0:
            fsi += 10

    # EMI burden
    if salary > 0:

        emi_ratio = (emi / salary) * 100

        if emi_ratio < 30:
            fsi += 30
        elif emi_ratio < 50:
            fsi += 15

    # Cheque bounce behavior
    if behavior.get("bounce_count", 0) == 0:
        fsi += 20

    # Negative balance behaviour
    if behavior.get("negative_balance_count", 0) == 0:
        fsi += 20

    fsi = max(0, min(fsi, 100))

    # -------------------------------------
    # Stability Tag
    # -------------------------------------

    if fsi >= 75:
        stability = "Highly Stable"

    elif fsi >= 55:
        stability = "Stable"

    elif fsi >= 35:
        stability = "Average"

    else:
        stability = "Financially Stressed"

    # -------------------------------------
    # Attach indicators
    # -------------------------------------

    result["financial_indicators"] = {

        "financial_strength_index": round(fsi, 2),

        "stability_tag": stability
    }

    return result


# =====================================================
# SAFE DATE PARSER
# =====================================================

def parse_date_safe(date_str):

    try:

        if not date_str:
            return datetime.min

        return datetime.strptime(date_str, "%d/%m/%y")

    except:
        return datetime.min


# =====================================================
# EMPTY RESPONSE TEMPLATE
# =====================================================

def empty_response():

    return {

        "statement_summary": {},

        "income_analysis": {},

        "expense_analysis": {},

        "behavior_analysis": {},

        "risk_summary": {},

        "financial_indicators": {},

        "chart_data": {}
    }
