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
# SMART TRANSACTION EXTRACTION (HDFC Compatible)
# =============================================

def extract_transactions(text):

    transactions = []
    lines = text.split("\n")

    current_txn = None

    for line in lines:

        clean_line = line.strip()
        lower_line = clean_line.lower()

        # Skip obvious non-transaction lines
        if any(skip in lower_line for skip in [
            "statement of account",
            "account branch",
            "opening balance",
            "closing balance",
            "statement summary",
            "generated on",
            "page no",
            "hdfc bank limited",
            "ifsc",
            "micr",
            "address",
            "nomination"
        ]):
            continue

        # Detect new transaction by date
        date_match = re.match(r"\d{2}/\d{2}/\d{2}", clean_line)

        if date_match:

            # Save previous txn
            if current_txn:
                transactions.append(current_txn)

            numbers = re.findall(r"-?\d{1,3}(?:,\d{3})*(?:\.\d+)?", clean_line)

            if len(numbers) < 2:
                continue

            # Last number is usually closing balance
            balance = float(numbers[-1].replace(",", ""))

            # Second last number is transaction amount
            amount = float(numbers[-2].replace(",", ""))

            debit = 0
            credit = 0

            # Determine debit/credit
            # If balance decreased → debit
            # If balance increased → credit
            # Since we don't know previous balance here,
            # use keyword logic fallback

            if any(word in lower_line for word in [
                "upi", "ach", "o-mf", "debit", "payment", "billpay"
            ]):
                debit = amount
            else:
                credit = amount

            current_txn = {
                "date": date_match.group(),
                "description": clean_line,
                "debit": debit,
                "credit": credit,
                "balance": balance
            }

        else:
            # Continuation line → append to description
            if current_txn:
                current_txn["description"] += " " + clean_line

    # Append last transaction
    if current_txn:
        transactions.append(current_txn)

    return transactions
