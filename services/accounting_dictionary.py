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
"tca",
"total ca",
"current asset total"
],

"current_liabilities":[
"current liabilities",
"total current liabilities",
"current liability",
"tcl",
"total cl",
"current liability total"
],

"inventory":[
"inventory",
"inventories",
"stock",
"stock in trade",
"stock-in-trade",
"closing stock",
"opening stock",
"finished goods",
"raw material",
"raw material stock",
"work in progress",
"wip",
"goods inventory"
],

"receivables":[
"trade receivables",
"sundry debtors",
"accounts receivable",
"account receivable",
"debtors",
"receivables",
"book debts",
"trade debtors"
],

"payables":[
"trade payables",
"sundry creditors",
"accounts payable",
"account payable",
"creditors",
"payables",
"trade creditors"
],

"cash_bank":[
"cash and bank",
"cash and bank balance",
"cash and cash equivalents",
"cash balance",
"bank balance",
"cash in hand",
"cash at bank"
],

"bank_credit":[
"bank borrowings",
"borrowings",
"cash credit",
"cc limit",
"working capital loan",
"bank overdraft",
"secured loan",
"short term borrowings",
"cc account",
"od account"
],

"other_current_assets":[
"other current assets",
"short term loans and advances",
"loans and advances",
"advances",
"other loans and advances",
"advance to suppliers",
"advance recoverable"
],

"other_current_liabilities":[
"other current liabilities",
"short term provisions",
"provisions",
"other liabilities",
"statutory dues",
"outstanding expenses"
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
"operating revenue",
"total revenue",
"income from operations"
],

"other_income":[
"other income",
"non operating income",
"misc income",
"miscellaneous income",
"other revenue"
],

"cogs":[
"cost of goods sold",
"cost of sales",
"cost of materials consumed",
"direct cost",
"purchase of stock in trade",
"cost of goods",
"material consumed",
"purchase cost"
],

"operating_expenses":[
"operating expenses",
"administrative expenses",
"selling expenses",
"other expenses",
"employee benefit expenses",
"staff cost"
],

"gross_profit":[
"gross profit",
"gp"
],

"ebitda":[
"ebitda",
"earnings before interest tax depreciation amortization",
"operating profit"
],

"depreciation":[
"depreciation",
"depreciation expense",
"depreciation and amortization"
],

"interest_expense":[
"interest",
"finance cost",
"finance charges",
"interest expense",
"interest on loans"
],

"profit_before_tax":[
"profit before tax",
"pbt",
"profit before taxation"
],

"net_profit":[
"net profit",
"profit after tax",
"pat",
"net income",
"profit for the year",
"profit after taxation"
],


# ==========================================================
# BANKING / STATEMENT
# ==========================================================

"salary_income":[
"salary",
"salary credit",
"salary deposit",
"salary transfer"
],

"upi_spend":[
"upi",
"upi payment",
"upi transfer",
"upi txn"
],

"loan_emi":[
"emi",
"loan installment",
"installment",
"loan emi"
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
"figures in thousands",
"amount in thousand"
],

"lakh":[
"in lakh",
"in lakhs",
"amounts in lakhs",
"figures in lakhs",
"amount in lakh"
],

"million":[
"in million",
"in millions",
"amounts in million"
],

"crore":[
"in crore",
"in crores",
"amounts in crores",
"figures in crores"
]

}
