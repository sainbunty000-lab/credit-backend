import pdfplumber
import re
from io import BytesIO

from .banking_dictionary import CREDIT_KEYWORDS, DEBIT_KEYWORDS


# ====================================================
# MAIN ENTRY
# ====================================================

def parse_banking_file(file_bytes):

    transactions = parse_table_statement(file_bytes)

    if not transactions:
        transactions = universal_parser(file_bytes)

    # Apply balance validation correction
    transactions = validate_balance_flow(transactions)

    return transactions


# ====================================================
# SAFE FLOAT
# ====================================================

def to_float(value):

    try:
        return float(str(value).replace(",", "").strip())
    except:
        return 0.0


# ====================================================
# TABLE PARSER
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
# UNIVERSAL PARSER
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
# KEYWORD CLASSIFICATION
# ====================================================

def classify_transaction(text, amount, previous_balance=None, current_balance=None):

    text = text.lower()

    for keyword in CREDIT_KEYWORDS:
        if keyword in text:
            return 0, amount

    for keyword in DEBIT_KEYWORDS:
        if keyword in text:
            return amount, 0

    # Balance movement fallback
    if previous_balance is not None and current_balance is not None:

        if current_balance > previous_balance:
            return 0, amount

        if current_balance < previous_balance:
            return amount, 0

    return 0, amount


# ====================================================
# BALANCE VALIDATION ENGINE
# ====================================================

def validate_balance_flow(transactions):

    if not transactions:
        return transactions

    corrected = []

    prev_balance = None

    for txn in transactions:

        debit = txn["debit"]
        credit = txn["credit"]
        balance = txn["balance"]

        if prev_balance is not None:

            expected_balance = prev_balance + credit - debit

            # If mismatch, swap debit/credit
            if abs(expected_balance - balance) > 1:

                corrected_debit = credit
                corrected_credit = debit

                expected_balance = prev_balance + corrected_credit - corrected_debit

                if abs(expected_balance - balance) < 1:

                    debit = corrected_debit
                    credit = corrected_credit

        corrected.append({
            "date": txn["date"],
            "description": txn["description"],
            "debit": debit,
            "credit": credit,
            "balance": balance
        })

        prev_balance = balance

    return corrected
