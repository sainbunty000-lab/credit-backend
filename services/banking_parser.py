import pdfplumber
import re
from io import BytesIO


# =========================================
# MAIN ENTRY
# =========================================

def parse_banking_file(file_bytes):

    transactions = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:

        for page in pdf.pages:

            table = page.extract_table()

            if not table:
                continue

            header = [str(c).lower() for c in table[0]]

            for row in table[1:]:

                if not row or len(row) < 6:
                    continue

                date = str(row[0]).strip()

                if not re.match(r"\d{2}/\d{2}/\d{2}", date):
                    continue

                narration = str(row[1]).strip()

                debit = to_float(row[4])
                credit = to_float(row[5])
                balance = to_float(row[6]) if len(row) > 6 else 0

                transactions.append({
                    "date": date,
                    "description": narration,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance
                })

    return transactions


# =========================================
# SAFE FLOAT
# =========================================

def to_float(val):

    try:
        return float(str(val).replace(",", "").strip())
    except:
        return 0
