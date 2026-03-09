# ==========================================================
# ACCOUNTING KEYWORDS DICTIONARY
# Used for financial statement extraction
# ==========================================================

ACCOUNTING_KEYWORDS = {

# ==========================================================
# BALANCE SHEET
# ==========================================================

"current_assets":[
"current assets",
"total current assets",
"current asset",
"tca"
],

"current_liabilities":[
"current liabilities",
"total current liabilities",
"current liability",
"tcl"
],

"inventory":[
"inventory",
"inventories",
"stock",
"stock in trade",
"closing stock",
"stock-in-trade",
"finished goods",
"raw material stock"
],

"receivables":[
"trade receivables",
"sundry debtors",
"accounts receivable",
"debtors",
"receivables",
"book debts"
],

"payables":[
"trade payables",
"sundry creditors",
"accounts payable",
"creditors",
"payables"
],

"cash_bank":[
"cash and bank",
"cash and cash equivalents",
"cash balance",
"bank balance",
"cash in hand"
],

"bank_credit":[
"bank borrowings",
"borrowings",
"cash credit",
"cc limit",
"working capital loan",
"bank overdraft",
"secured loan",
"short term borrowings"
],

"other_current_assets":[
"other current assets",
"short term loans and advances",
"loans and advances",
"advances",
"other loans and advances"
],

"other_current_liabilities":[
"other current liabilities",
"short term provisions",
"provisions",
"other liabilities"
],


# ==========================================================
# PROFIT & LOSS
# ==========================================================

"annual_sales":[
"sales",
"net sales",
"total sales",
"gross sales",
"revenue",
"revenue from operations",
"turnover",
"sales turnover",
"sale of products",
"operating revenue"
],

"other_income":[
"other income",
"non operating income",
"misc income"
],

"cogs":[
"cost of goods sold",
"cost of sales",
"cost of materials consumed",
"direct cost",
"purchase of stock in trade"
],

"operating_expenses":[
"operating expenses",
"administrative expenses",
"selling expenses",
"other expenses"
],

"gross_profit":[
"gross profit",
"gp"
],

"ebitda":[
"ebitda",
"earnings before interest tax depreciation amortization"
],

"depreciation":[
"depreciation",
"depreciation expense"
],

"interest_expense":[
"interest",
"finance cost",
"finance charges",
"interest expense"
],

"profit_before_tax":[
"profit before tax",
"pbt"
],

"net_profit":[
"net profit",
"profit after tax",
"pat",
"net income",
"profit for the year"
],


# ==========================================================
# BANKING / STATEMENT
# ==========================================================

"salary_income":[
"salary",
"salary credit",
"salary deposit"
],

"upi_spend":[
"upi",
"upi payment",
"upi transfer"
],

"loan_emi":[
"emi",
"loan installment",
"installment"
]

}


# ==========================================================
# UNIT SCALE DETECTION
# Detect statements mentioning values in thousand/lakh/etc
# ==========================================================

UNIT_SCALE_KEYWORDS = {

"thousand":[
"in thousand",
"in thousands",
"amounts in thousand",
"amounts in thousands",
"figures in thousand",
"figures in thousands"
],

"lakh":[
"in lakh",
"in lakhs",
"amounts in lakhs",
"figures in lakhs"
],

"million":[
"in million",
"in millions"
],

"crore":[
"in crore",
"in crores"
]

}
