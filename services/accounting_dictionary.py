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
"current asset total",
"total of current assets"
],

"current_liabilities":[
"current liabilities",
"total current liabilities",
"current liability",
"tcl",
"total cl",
"current liability total",
"total of current liabilities"
],

# ----------------------------------------------------------
# INVENTORY
# ----------------------------------------------------------

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
"goods inventory",
"inventory of goods",
"inventory balance"
],

# ----------------------------------------------------------
# RECEIVABLES
# ----------------------------------------------------------

"receivables":[
"trade receivables",
"sundry debtors",
"accounts receivable",
"account receivable",
"debtors",
"receivables",
"book debts",
"trade debtors",
"receivable from customers",
"amount receivable"
],

# ----------------------------------------------------------
# PAYABLES
# ----------------------------------------------------------

"payables":[
"trade payables",
"sundry creditors",
"accounts payable",
"account payable",
"creditors",
"payables",
"trade creditors",
"amount payable",
"payable to suppliers"
],

# ----------------------------------------------------------
# CASH & BANK
# ----------------------------------------------------------

"cash_bank":[
"cash and bank",
"cash & bank",
"cash and bank balance",
"cash and cash equivalents",
"cash balance",
"bank balance",
"cash in hand",
"cash at bank",
"bank balances",
"cash balances",
"cash and bank balances"
],

# ----------------------------------------------------------
# BANK CREDIT
# ----------------------------------------------------------

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
"od account",
"bank loan",
"loan from bank",
"cash credit facility"
],

# ----------------------------------------------------------
# OTHER CURRENT ASSETS
# ----------------------------------------------------------

"other_current_assets":[
"other current assets",
"short term loans and advances",
"loans and advances",
"loans & advances",
"advances",
"other loans and advances",
"advance to suppliers",
"advance recoverable",
"prepaid expenses",
"advance payments"
],

# ----------------------------------------------------------
# OTHER CURRENT LIABILITIES
# ----------------------------------------------------------

"other_current_liabilities":[
"other current liabilities",
"short term provisions",
"provisions",
"other liabilities",
"statutory dues",
"outstanding expenses",
"accrued expenses",
"provision for tax",
"provision for taxation",
"provision for expenses"
],


# ==========================================================
# PROFIT & LOSS
# ==========================================================

# ----------------------------------------------------------
# SALES
# ----------------------------------------------------------

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
"income from operations",
"revenue from sale",
"sales income"
],

# ----------------------------------------------------------
# OTHER INCOME
# ----------------------------------------------------------

"other_income":[
"other income",
"non operating income",
"misc income",
"miscellaneous income",
"other revenue",
"non operational income"
],

# ----------------------------------------------------------
# COST OF GOODS SOLD
# ----------------------------------------------------------

"cogs":[
"cost of goods sold",
"cost of sales",
"cost of materials consumed",
"direct cost",
"purchase of stock in trade",
"cost of goods",
"material consumed",
"purchase cost",
"cost of material",
"purchase of goods"
],

# ----------------------------------------------------------
# OPERATING EXPENSES
# ----------------------------------------------------------

"operating_expenses":[
"operating expenses",
"administrative expenses",
"selling expenses",
"other expenses",
"employee benefit expenses",
"staff cost",
"salaries and wages",
"office expenses",
"general expenses"
],

# ----------------------------------------------------------
# GROSS PROFIT
# ----------------------------------------------------------

"gross_profit":[
"gross profit",
"gp",
"gross income"
],

# ----------------------------------------------------------
# EBITDA
# ----------------------------------------------------------

"ebitda":[
"ebitda",
"earnings before interest tax depreciation amortization",
"operating profit",
"earnings before interest tax depreciation"
],

# ----------------------------------------------------------
# DEPRECIATION
# ----------------------------------------------------------

"depreciation":[
"depreciation",
"depreciation expense",
"depreciation and amortization",
"amortization"
],

# ----------------------------------------------------------
# INTEREST
# ----------------------------------------------------------

"interest_expense":[
"interest",
"finance cost",
"finance charges",
"interest expense",
"interest on loans",
"bank interest"
],

# ----------------------------------------------------------
# PBT
# ----------------------------------------------------------

"profit_before_tax":[
"profit before tax",
"pbt",
"profit before taxation",
"profit before income tax"
],

# ----------------------------------------------------------
# PAT
# ----------------------------------------------------------

"net_profit":[
"net profit",
"profit after tax",
"pat",
"net income",
"profit for the year",
"profit after taxation",
"profit after income tax"
],


# ==========================================================
# BANKING / STATEMENT
# ==========================================================

"salary_income":[
"salary",
"salary credit",
"salary deposit",
"salary transfer",
"salary payment"
],

"upi_spend":[
"upi",
"upi payment",
"upi transfer",
"upi txn",
"gpay",
"phonepe",
"paytm"
],

"loan_emi":[
"emi",
"loan installment",
"installment",
"loan emi",
"loan repayment"
]

}


# ==========================================================
# UNIT SCALE DETECTION
# ==========================================================

UNIT_SCALE_KEYWORDS = {

"thousand":[
"in thousand",
"in thousands",
"amounts in thousand",
"amounts in thousands",
"figures in thousand",
"figures in thousands",
"amount in thousand",
"amount in thousands"
],

"lakh":[
"in lakh",
"in lakhs",
"amounts in lakhs",
"figures in lakhs",
"amount in lakh",
"amount in lakhs"
],

"million":[
"in million",
"in millions",
"amounts in million",
"figures in million"
],

"crore":[
"in crore",
"in crores",
"amounts in crores",
"figures in crores",
"amount in crore"
]

}
