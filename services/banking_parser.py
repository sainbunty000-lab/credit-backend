import pdfplumber
from io import BytesIO
import re


# =============================================
# MAIN ENTRY
# =============================================

def parse_banking_file(file_bytes, filename):

    filename = filename.lower()

    if not filename.endswith(".pdf"):
        raise ValueError("Only PDF supported")

    text = extract_full_text(file_bytes)

    transactions = extract_transactions(text)

    return transactions


# =============================================
# EXTRACT FULL TEXT
# =============================================

def extract_full_text(file_bytes):

    text = ""

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


# =============================================
# STRICT TRANSACTION EXTRACTION
# =============================================

def extract_transactions(text):

    transactions = []
    lines = text.split("\n")

    for line in lines:

        lower_line = line.lower()

        # Skip obvious summary lines
        if any(skip in lower_line for skip in [
            "total debit",
            "total credit",
            "opening balance",
            "closing balance",
            "statement summary"
        ]):
            continue

        # Detect date ANYWHERE in line
        date_match = re.search(r"\d{2}/\d{2}/\d{2}", line)
        if not date_match:
            continue

        numbers = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", line)

        if len(numbers) < 2:
            continue

        txn_amount = float(numbers[-2].replace(",", ""))

        debit = 0
        credit = 0

        if "dr" in lower_line:
            debit = txn_amount
        elif "cr" in lower_line:
            credit = txn_amount
        else:
            continue

        transactions.append({
            "date": date_match.group(),
            "credit": credit,
            "debit": debit,
            "description": line.strip()
        })

    return transactions
