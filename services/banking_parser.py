import pdfplumber
import re
from io import BytesIO

from .banking_dictionary import CREDIT_KEYWORDS, DEBIT_KEYWORDS


# =====================================
# MAIN ENTRY
# =====================================

def parse_banking_file(file_bytes):

    bank = detect_bank(file_bytes)

    if bank == "hdfc":
        transactions = parse_hdfc(file_bytes)
    else:
        transactions = universal_parser(file_bytes)

    return transactions


# =====================================
# BANK DETECTION
# =====================================

def detect_bank(file_bytes):

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:

        text = pdf.pages[0].extract_text().lower()

        if "hdfc bank" in text:
            return "hdfc"

        if "state bank of india" in text:
            return "sbi"

        if "icici bank" in text:
            return "icici"

        if "axis bank" in text:
            return "axis"

        if "kotak mahindra bank" in text:
            return "kotak"

    return "unknown"


# =====================================
# SAFE FLOAT
# =====================================

def to_float(val):

    try:
        return float(str(val).replace(",", "").strip())
    except:
        return 0


# =====================================
# HDFC TABLE PARSER
# =====================================

def parse_hdfc(file_bytes):

    transactions = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:

                for row in table:

                    if not row or len(row) < 7:
                        continue

                    if "date" in str(row[0]).lower():
                        continue

                    date = str(row[0]).strip()

                    if "/" not in date:
                        continue

                    narration = str(row[1]).strip()

                    debit = to_float(row[4])
                    credit = to_float(row[5])
                    balance = to_float(row[6])

                    transactions.append({
                        "date": date,
                        "description": narration,
                        "debit": debit,
                        "credit": credit,
                        "balance": balance
                    })

    return transactions


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

                if re.match(r"\d{2}/\d{2}/\d{2}", line):

                    numbers = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", line)

                    if len(numbers) < 2:
                        continue

                    balance = float(numbers[-1].replace(",", ""))
                    amount = float(numbers[-2].replace(",", ""))

                    debit, credit = classify_transaction(line, amount)

                    transactions.append({
                        "date": line[:8],
                        "description": line,
                        "debit": debit,
                        "credit": credit,
                        "balance": balance
                    })

    return transactions


# =====================================
# CLASSIFIER
# =====================================

def classify_transaction(text, amount, previous_balance=None, current_balance=None):

    text = text.lower()

    # 1️⃣ Credit keyword check
    for k in CREDIT_KEYWORDS:
        if k in text:
            return 0, amount

    # 2️⃣ Debit keyword check
    for k in DEBIT_KEYWORDS:
        if k in text:
            return amount, 0

    # 3️⃣ Balance validation fallback
    if previous_balance is not None and current_balance is not None:

        if current_balance > previous_balance:
            return 0, amount

        if current_balance < previous_balance:
            return amount, 0

    # 4️⃣ Final fallback (neutral)
    return 0, amount
