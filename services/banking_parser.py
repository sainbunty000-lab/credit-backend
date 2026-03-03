import pdfplumber
from io import BytesIO
import re


# ======================================================
# MAIN ENTRY
# ======================================================
def parse_banking_file(file_bytes, filename):

    filename = filename.lower()

    if filename.endswith(".pdf"):
        return parse_pdf_text_based(file_bytes)

    else:
        raise ValueError("Only PDF supported for full analysis endpoint")


# ======================================================
# TEXT-BASED HDFC SAFE PARSER
# ======================================================
def parse_pdf_text_based(file_bytes):

    transactions = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")

            for line in lines:

                # Detect transaction row (starts with date)
                if not re.search(r"\d{2}/\d{2}/\d{2}", line):
                    continue

                numbers = extract_money_values(line)

                if len(numbers) < 2:
                    continue

                txn_amount = numbers[-2]   # second last = txn
                balance = numbers[-1]      # last = balance

                debit = 0
                credit = 0

                line_lower = line.lower()

                if "dr" in line_lower:
                    debit = txn_amount
                elif "cr" in line_lower:
                    credit = txn_amount
                else:
                    # Fallback logic
                    if txn_amount < 0:
                        debit = abs(txn_amount)
                    else:
                        credit = txn_amount

                if debit == 0 and credit == 0:
                    continue

                transactions.append({
                    "date": re.search(r"\d{2}/\d{2}/\d{2}", line).group(),
                    "credit": credit,
                    "debit": debit,
                    "description": line.strip()
                })

    return transactions


# ======================================================
# MONEY EXTRACTOR
# ======================================================
def extract_money_values(text):

    matches = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", text)

    values = []

    for m in matches:
        try:
            val = float(m.replace(",", ""))
            if val < 100000000:  # sanity filter
                values.append(val)
        except:
            continue

    return values
