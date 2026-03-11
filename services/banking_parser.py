import pdfplumber
import re
from io import BytesIO
from datetime import datetime


# =====================================================
# DATE PATTERNS (MULTIPLE BANK FORMATS)
# =====================================================

DATE_PATTERNS = [
    r"\d{2}/\d{2}/\d{2}",
    r"\d{2}/\d{2}/\d{4}",
    r"\d{2}-\d{2}-\d{2}",
    r"\d{2}-\d{2}-\d{4}"
]


# =====================================================
# MAIN ENTRY
# =====================================================

def parse_banking_file(file_bytes):

    transactions = []

    try:

        with pdfplumber.open(BytesIO(file_bytes)) as pdf:

            for page in pdf.pages:

                # ---------------------------------
                # Try table extraction first
                # ---------------------------------
                tables = page.extract_tables()

                if tables:

                    for table in tables:

                        for row in table:

                            txn = parse_table_row(row)

                            if txn:
                                transactions.append(txn)

                # ---------------------------------
                # Fallback to text parsing
                # ---------------------------------

                text = page.extract_text()

                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:

                    txn = parse_text_line(line, transactions)

                    if txn:
                        transactions.append(txn)

    except:
        return []

    return transactions


# =====================================================
# TABLE ROW PARSER
# =====================================================

def parse_table_row(row):

    if not row:
        return None

    try:

        date = row[0]

        if not is_date(date):
            return None

        description = str(row[1] or "").strip()

        debit = normalize_number(row[2])
        credit = normalize_number(row[3])
        balance = normalize_number(row[4])

        return {
            "date": date,
            "description": description,
            "debit": debit,
            "credit": credit,
            "balance": balance
        }

    except:
        return None


# =====================================================
# TEXT LINE PARSER
# =====================================================

def parse_text_line(line, transactions):

    if not is_date_line(line):
        return None

    numbers = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", line)

    if len(numbers) < 2:
        return None

    balance = normalize_number(numbers[-1])
    amount = normalize_number(numbers[-2])

    debit = 0
    credit = 0

    # ---------------------------------
    # Determine debit / credit
    # ---------------------------------

    if transactions:

        prev_balance = transactions[-1]["balance"]

        if balance > prev_balance:
            credit = amount
        else:
            debit = amount

    else:

        credit = amount

    # ---------------------------------
    # Extract narration
    # ---------------------------------

    date_match = re.search(get_date_regex(), line)

    if not date_match:
        return None

    date = date_match.group()

    narration = line.replace(date, "").strip()

    return {
        "date": date,
        "description": narration,
        "debit": debit,
        "credit": credit,
        "balance": balance
    }


# =====================================================
# DATE DETECTION
# =====================================================

def is_date_line(line):

    for pattern in DATE_PATTERNS:

        if re.match(pattern, line):
            return True

    return False


def is_date(value):

    if not value:
        return False

    value = str(value)

    for pattern in DATE_PATTERNS:

        if re.match(pattern, value):
            return True

    return False


def get_date_regex():

    return "(" + "|".join(DATE_PATTERNS) + ")"


# =====================================================
# NUMBER NORMALIZATION
# =====================================================

def normalize_number(value):

    try:

        if value is None:
            return 0

        value = str(value)

        value = value.replace(",", "")
        value = value.replace("₹", "")
        value = value.strip()

        return float(value)

    except:
        return 0
