# ==========================================================
# BANKING KEYWORD DICTIONARY
# Used for bank statement categorization
# ==========================================================


# ==========================================================
# CREDIT TRANSACTIONS
# ==========================================================

CREDIT_KEYWORDS = [

    # Salary
    "salary",
    "salary credit",
    "sal credit",
    "salary transfer",
    "payroll",
    "wages",

    # Transfers
    "transfer from",
    "neft cr",
    "rtgs cr",
    "imps cr",
    "imps credit",
    "p2a credit",

    # Incoming UPI
    "upi cr",
    "upi received",
    "upi collect",
    "received via upi",

    # Deposits
    "cash deposit",
    "deposit",
    "cheque deposit",
    "chq deposit",

    # Refunds
    "refund",
    "refund credit",
    "reversal",
    "chargeback",

    # Investments
    "redemption",
    "mf redemption",
    "dividend",
    "mutual fund redemption",

    # Cashback
    "cashback",
    "reward",
    "reward credit",

    # Interest
    "interest",
    "interest credit",
    "int cr",

    # Business income
    "commission",
    "bonus",
    "incentive",
    "reimbursement",
    "consulting fee",
    "professional fee",

    # Incoming payments
    "received",
    "incoming",
    "payment received"
]


# ==========================================================
# DEBIT TRANSACTIONS
# ==========================================================

DEBIT_KEYWORDS = [

    # UPI / Wallets
    "upi",
    "upi payment",
    "upi transfer",
    "paytm",
    "phonepe",
    "gpay",
    "google pay",
    "amazon pay",

    # ATM withdrawals
    "atm",
    "atm withdrawal",
    "cash withdrawal",
    "atm wdl",

    # POS / card
    "pos",
    "purchase",
    "debit card",
    "card payment",
    "pos transaction",

    # Online shopping
    "amazon",
    "flipkart",
    "swiggy",
    "zomato",
    "myntra",

    # Transfers
    "transfer",
    "neft",
    "rtgs",
    "imps",
    "p2a",

    # EMI / Loans
    "emi",
    "loan emi",
    "nach",
    "ach debit",
    "ecs",
    "loan repayment",
    "finance",

    # Investments
    "sip",
    "mutual fund sip",
    "o-mf",

    # Utilities
    "bill",
    "bill payment",
    "electricity",
    "gas",
    "water",

    # Insurance
    "insurance",
    "premium",

    # Rent
    "rent",

    # Charges
    "charges",
    "bank charge",
    "sms charge",
    "debit charge",
    "processing fee",

    # Subscriptions
    "netflix",
    "spotify",
    "prime",

    # Travel
    "uber",
    "ola",
    "irctc",
    "flight booking"
]


# ==========================================================
# EMI DETECTION
# ==========================================================

EMI_KEYWORDS = [

    "emi",
    "loan emi",
    "nach",
    "ach debit",
    "ecs",
    "loan repayment",
    "finance",
    "capital first",
    "bajaj finance",
    "home loan",
    "personal loan"
]


# ==========================================================
# SALARY DETECTION
# ==========================================================

SALARY_KEYWORDS = [

    "salary",
    "sal credit",
    "salary credit",
    "salary transfer",
    "payroll",
    "wages"
]


# ==========================================================
# BOUNCE / RETURN
# ==========================================================

BOUNCE_KEYWORDS = [

    "return",
    "bounce",
    "cheque return",
    "insufficient funds",
    "return charges",
    "payment returned"
]
