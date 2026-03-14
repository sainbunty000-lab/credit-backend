cat > services/wc_required_fields.py <<'PY'
WC_REQUIRED_INPUT_FIELDS = [
    "current_assets",
    "current_liabilities",
    "inventory",
    "receivables",
    "payables",
    "cash_bank",
    "bank_credit",
    "annual_sales",
    "other_income",
    "operating_expenses",
    "interest_expense",
    "depreciation",
    "tax",
]
PY
