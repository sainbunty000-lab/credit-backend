from datetime import datetime
from services.banking_service import analyze_banking


# =========================================
# MASTER ANALYZER ENTRY
# =========================================

def analyze_transactions(transactions):

    if not transactions or not isinstance(transactions, list):
        return empty_response()

    # -------------------------------------
    # Clean & normalize
    # -------------------------------------
    cleaned = normalize_transactions(transactions)

    # -------------------------------------
    # Sort by date
    # -------------------------------------
    cleaned.sort(key=lambda x: parse_date_safe(x.get("date")))

    # -------------------------------------
    # Banking Analysis
    # -------------------------------------
    banking_result = analyze_banking(cleaned)

    # -------------------------------------
    # Add derived financial indicators
    # -------------------------------------
    enriched = enrich_with_indicators(banking_result)

    return enriched


# =========================================
# NORMALIZATION
# =========================================

def normalize_transactions(transactions):

    normalized = []

    for txn in transactions:

        try:
            normalized.append({
                "date": txn.get("date"),
                "description": str(txn.get("description", "")).strip(),
                "credit": float(txn.get("credit", 0) or 0),
                "debit": float(txn.get("debit", 0) or 0),
                "balance": float(txn.get("balance", 0) or 0)
            })
        except:
            continue

    return normalized


# =========================================
# DERIVED FINANCIAL INDICATORS
# =========================================

def enrich_with_indicators(result):

    summary = result.get("statement_summary", {})
    income = result.get("income_analysis", {})
    expense = result.get("expense_analysis", {})
    behavior = result.get("behavior_analysis", {})
    risk = result.get("risk_summary", {})

    salary = income.get("salary_income", 0)
    emi = expense.get("emi_total", 0)
    net = summary.get("net_surplus", 0)

    # -------------------------------------
    # Financial Strength Index (FSI)
    # -------------------------------------
    fsi = 0

    if salary > 0:
        savings_ratio = (net / salary) * 100 if salary else 0

        if savings_ratio > 20:
            fsi += 30
        elif savings_ratio > 10:
            fsi += 20
        elif savings_ratio > 0:
            fsi += 10

    if salary > 0:
        emi_ratio = (emi / salary) * 100
        if emi_ratio < 30:
            fsi += 30
        elif emi_ratio < 50:
            fsi += 15

    if behavior.get("bounce_count", 0) == 0:
        fsi += 20

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
    # Attach Indicators
    # -------------------------------------
    result["financial_indicators"] = {
        "financial_strength_index": fsi,
        "stability_tag": stability
    }

    return result


# =========================================
# SAFE DATE PARSER
# =========================================

def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%y")
    except:
        return datetime.min


# =========================================
# EMPTY RESPONSE
# =========================================

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
  
