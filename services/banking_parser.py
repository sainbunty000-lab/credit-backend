import pdfplumber
import re
from io import BytesIO


# =====================================
# MAIN ENTRY
# =====================================

def parse_banking_file(file_bytes):

    transactions = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            for line in lines:

                # Detect transaction line
                if not re.match(r"\d{2}/\d{2}/\d{2}", line):
                    continue

                parts = line.split()

                if len(parts) < 4:
                    continue

                date = parts[0]

                numbers = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", line)

                if len(numbers) < 2:
                    continue

                balance = to_float(numbers[-1])
                amount = to_float(numbers[-2])

                debit = 0
                credit = 0

                # Determine debit/credit using balance movement
                if transactions:

                    prev_balance = transactions[-1]["balance"]

                    if balance > prev_balance:
                        credit = amount
                    else:
                        debit = amount

                else:
                    credit = amount

                narration = line[len(date):].strip()

                transactions.append({
                    "date": date,
                    "description": narration,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance
                })

    return transactions


# =====================================
# SAFE FLOAT
# =====================================

def to_float(val):

    try:
        return float(str(val).replace(",", "").strip())
    except:
        return 0
