# accounting_dictionary.py

ACCOUNTING_MAP = {
    "current_assets": [
        "current assets", "total current assets", "short term assets", 
        "circulating assets", "inventory + receivables", "cash and bank balances"
    ],
    "current_liabilities": [
        "current liabilities", "total current liabilities", "short term liabilities",
        "trade payables", "sundry creditors", "short term borrowings"
    ],
    "annual_sales": [
        "sales", "turnover", "revenue from operations", "gross receipts",
        "total income", "net sales"
    ],
    "documented_income": [
        "gross total income", "taxable income", "net profit as per p&l",
        "income from salary", "business income"
    ],
    "tax_paid": [
        "income tax", "tax paid", "provision for tax", "taxes"
    ]
}

# Banking Keywords for Hygiene Analysis
BANKING_KEYWORDS = {
    "emi": ["emi", "loan payment", "nach", "m-pay", "repayment"],
    "bounce": ["bounce", "return", "chq ret", "insufficient funds", "reversal"],
    "cash": ["cash dep", "self", "cash deposit", "cts", "cdm"]
}
