import pdfplumber
import re
from io import BytesIO

from .banking_dictionary import CREDIT_KEYWORDS, DEBIT_KEYWORDS


# =====================================
# MAIN ENTRY
# =====================================

def parse_banking_file(file_bytes):

    transactions = universal_parser(file_bytes)

    return transactions


# =====================================
# SAFE FLOAT
# =====================================

def to_float(val):

    try:
        return float(str(val).replace(",", "").strip())
    except:
        return 0.0


# =====================================
# UNIVERSAL PARSER
# =====================================

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


# =====================================
# CLASSIFICATION ENGINE
# =====================================

def classify_transaction(text, amount, previous_balance=None, current_balance=None):

    text = text.lower()

    # --------------------------------
    # Credit keywords
    # --------------------------------

    for keyword in CREDIT_KEYWORDS:
        if keyword in text:
            return 0, amount

    # --------------------------------
    # Debit keywords
    # --------------------------------

    for keyword in DEBIT_KEYWORDS:
        if keyword in text:
            return amount, 0

    # --------------------------------
    # Balance rule fallback
    # --------------------------------

    if previous_balance is not None and current_balance is not None:

        if current_balance > previous_balance:
            return 0, amount

        if current_balance < previous_balance:
            return amount, 0

    # --------------------------------
    # Default fallback
    # --------------------------------

    return 0, amount
