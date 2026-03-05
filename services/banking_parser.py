import pdfplumber
import re
from io import BytesIO


# =============================================
# MAIN ENTRY
# =============================================

def parse_banking_file(file_bytes, filename):

    bank = detect_bank(file_bytes)

    if bank == "hdfc":
        txns = parse_hdfc(file_bytes)

    elif bank == "sbi":
        txns = parse_sbi(file_bytes)

    elif bank == "icici":
        txns = parse_icici(file_bytes)

    elif bank == "axis":
        txns = parse_axis(file_bytes)

    elif bank == "kotak":
        txns = parse_kotak(file_bytes)

    else:
        txns = universal_parser(file_bytes)

    return txns


# =============================================
# BANK DETECTION
# =============================================

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


# =============================================
# SAFE FLOAT
# =============================================

def to_float(val):

    try:
        return float(str(val).replace(",", "").strip())
    except:
        return 0.0


# =============================================
# HDFC PARSER
# =============================================

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


# =============================================
# GENERIC BANK PARSER (SBI/ICICI/AXIS/KOTAK)
# =============================================

def parse_sbi(file_bytes):
    return universal_parser(file_bytes)


def parse_icici(file_bytes):
    return universal_parser(file_bytes)


def parse_axis(file_bytes):
    return universal_parser(file_bytes)


def parse_kotak(file_bytes):
    return universal_parser(file_bytes)


# =============================================
# UNIVERSAL FALLBACK PARSER
# =============================================

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

                    nums = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", line)

                    if len(nums) < 2:
                        continue

                    balance = float(nums[-1].replace(",", ""))
                    amount = float(nums[-2].replace(",", ""))

                    if detect_debit(line):
                        debit = amount
                        credit = 0
                    else:
                        credit = amount
                        debit = 0

                    transactions.append({
                        "date": line[:8],
                        "description": line,
                        "debit": debit,
                        "credit": credit,
                        "balance": balance
                    })

    return transactions


# =============================================
# DEBIT DETECTOR
# =============================================

def detect_debit(text):

    text = text.lower()

    keywords = [
        "upi",
        "ach",
        "payment",
        "debit",
        "bill",
        "atm",
        "withdraw",
        "pos",
        "transfer"
    ]

    for k in keywords:
        if k in text:
            return True

    return False
