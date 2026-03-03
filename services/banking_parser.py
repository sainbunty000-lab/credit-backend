import pdfplumber
from io import BytesIO
import re


# ==========================================================
# MAIN ENTRY
# ==========================================================
def parse_banking_file(file_bytes, filename):

    filename = filename.lower()

    if not filename.endswith(".pdf"):
        raise ValueError("Only PDF supported")

    full_text = extract_full_text(file_bytes)

    summary = extract_statement_summary(full_text)

    transactions = extract_transactions(full_text)

    return {
        "summary": summary,
        "transactions": transactions
    }


# ==========================================================
# EXTRACT FULL TEXT
# ==========================================================
def extract_full_text(file_bytes):

    text = ""

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


# ==========================================================
# EXTRACT SUMMARY BLOCK (AUTHORITATIVE TOTALS)
# ==========================================================
def extract_statement_summary(text):

    summary = {
        "opening_balance": 0,
        "closing_balance": 0,
        "total_credit": 0,
        "total_debit": 0,
        "credit_transactions": 0,
        "debit_transactions": 0
    }

    patterns = {
        "opening_balance": r"Opening Balance\s*[:\-]?\s*([\d,]+\.\d+)",
        "closing_balance": r"Closing Balance\s*[:\-]?\s*([\d,]+\.\d+)",
        "total_credit": r"Total Credits?\s*[:\-]?\s*([\d,]+\.\d+)",
        "total_debit": r"Total Debits?\s*[:\-]?\s*([\d,]+\.\d+)",
        "credit_transactions": r"Credit Transactions?\s*[:\-]?\s*(\d+)",
        "debit_transactions": r"Debit Transactions?\s*[:\-]?\s*(\d+)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            summary[key] = float(value.replace(",", ""))

    return summary


# ==========================================================
# EXTRACT TRANSACTIONS (FOR BEHAVIOUR ONLY)
# ==========================================================
def extract_transactions(text):

    transactions = []

    lines = text.split("\n")

    for line in lines:

        date_match = re.search(r"\d{2}/\d{2}/\d{2}", line)
        if not date_match:
            continue

        if "total debit" in line.lower():
            continue

        numbers = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", line)

        if len(numbers) < 2:
            continue

        txn_amount = float(numbers[-2].replace(",", ""))

        debit = 0
        credit = 0

        if "dr" in line.lower():
            debit = txn_amount
        elif "cr" in line.lower():
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
