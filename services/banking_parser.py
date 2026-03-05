import pdfplumber
import re
from io import BytesIO

from .banking_dictionary import CREDIT_KEYWORDS, DEBIT_KEYWORDS


# ====================================================
# MAIN ENTRY
# ====================================================

def parse_banking_file(file_bytes):

    # 1️⃣ Try structured table extraction
    transactions = parse_table_statement(file_bytes)

    if transactions:
        return transactions

    # 2️⃣ Fallback universal parser
    return universal_parser(file_bytes)


# ====================================================
# SAFE FLOAT
# ====================================================

def to_float(value):

    try:
        return float(str(value).replace(",", "").strip())
    except:
        return 0.0


# ====================================================
# TABLE PARSER (BEST ACCURACY)
# ====================================================

def parse_table_statement(file_bytes):

    transactions = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            if not tables:
                continue

            for table in tables:

                for row in table:

                    if not row or len(row) < 6:
                        continue

                    # Skip header rows
                    if "date" in str(row[0]).lower():
                        continue

                    date = str(row[0]).strip()

                    if "/" not in date:
                        continue

                    narration = str(row[1]).strip()

                    withdrawal = to_float(row[4])
                    deposit = to_float(row[5])

                    balance = 0
                    if len(row) > 6:
                        balance = to_float(row[6])

                    transactions.append({
                        "date": date,
                        "description": narration,
                        "debit": withdrawal,
                        "credit": deposit,
                        "balance": balance
                    })

    return transactions


# ====================================================
# UNIVERSAL PARSER (FALLBACK)
# ====================================================

def universal_parser(file_bytes):

    transactions = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            for line in lines:

                if not re.match(r"\d{2}/\d{2}/\d{2}", line):
                    continue

                numbers = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", line)

                if len(numbers) < 2:
                    continue

                balance = to_float(numbers[-1])
                amount = to_float(numbers[-2])

                previous_balance = (
                    transactions[-1]["balance"] if transactions else None
                )

                debit, credit = classify_transaction(
                    line,
                    amount,
                    previous_balance,
                    balance
                )

                transactions.append({
                    "date": line[:8],
                    "description": line.strip(),
                    "debit": debit,
                    "credit": credit,
                    "balance": balance
                })

    return transactions


# ====================================================
# CLASSIFICATION ENGINE
# ====================================================

def classify_transaction(text, amount, previous_balance=None, current_balance=None):

    text = text.lower()

    # 1️⃣ Credit keywords
    for keyword in CREDIT_KEYWORDS:
        if keyword in text:
            return 0, amount

    # 2️⃣ Debit keywords
    for keyword in DEBIT_KEYWORDS:
        if keyword in text:
            return amount, 0

    # 3️⃣ Balance movement rule
    if previous_balance is not None and current_balance is not None:

        if current_balance > previous_balance:
            return 0, amount

        if current_balance < previous_balance:
            return amount, 0

    # 4️⃣ Default fallback
    return 0, amount
