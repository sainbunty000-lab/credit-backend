import pandas as pd
import pdfplumber
import camelot
import tempfile
import re
from io import BytesIO


# ===============================
# MAIN ENTRY
# ===============================
def parse_banking_file(file_bytes, filename):

    filename = filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
        return normalize_dataframe(df)

    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(file_bytes))
        return normalize_dataframe(df)

    elif filename.endswith(".pdf"):
        return parse_pdf(file_bytes)

    else:
        raise ValueError("Unsupported file format")


# ===============================
# PDF PARSER (Camelot First)
# ===============================
def parse_pdf(file_bytes):

    # Save temp file for Camelot
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    # 1️⃣ Try Camelot
    try:
        tables = camelot.read_pdf(tmp_path, pages="all", flavor="stream")

        if tables and len(tables) > 0:
            all_data = []

            for table in tables:
                df = table.df
                parsed = parse_table_dataframe(df)
                all_data.extend(parsed)

            if all_data:
                return all_data

    except Exception:
        pass

    # 2️⃣ Fallback to pdfplumber text parsing
    return parse_pdf_text(file_bytes)


# ===============================
# TABLE PARSER (Camelot Output)
# ===============================
def parse_table_dataframe(df):

    df = df.replace("\n", " ", regex=True)
    transactions = []

    date_pattern = r"\d{2}/\d{2}/\d{2}"

    for _, row in df.iterrows():

        row_text = " ".join(row.astype(str).tolist())

        if not re.search(date_pattern, row_text):
            continue

        date_match = re.search(date_pattern, row_text)
        date = date_match.group() if date_match else None

        numbers = extract_numbers(row_text)

        if not numbers:
            continue

        credit, debit = detect_credit_debit(row_text, numbers)

        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "desc": row_text.strip(),
            "account": "PDF Account"
        })

    return transactions


# ===============================
# FALLBACK TEXT PARSER
# ===============================
def parse_pdf_text(file_bytes):

    text_data = ""

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_data += page.extract_text() or ""

    lines = text_data.split("\n")
    transactions = []

    date_pattern = r"\d{2}/\d{2}/\d{2}"

    for line in lines:

        if not re.search(date_pattern, line):
            continue

        date_match = re.search(date_pattern, line)
        date = date_match.group()

        numbers = extract_numbers(line)

        if not numbers:
            continue

        credit, debit = detect_credit_debit(line, numbers)

        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "desc": line.strip(),
            "account": "PDF Account"
        })

    return transactions


# ===============================
# SMART NUMBER EXTRACTOR
# ===============================
def extract_numbers(text):

    numbers = []

    for token in text.split():
        cleaned = token.replace(",", "")
        try:
            numbers.append(float(cleaned))
        except:
            continue

    return numbers


# ===============================
# SMART CREDIT / DEBIT DETECTION
# ===============================
def detect_credit_debit(text, numbers):

    credit = 0.0
    debit = 0.0

    text_upper = text.upper()

    # Case 1: DR / CR format
    if "CR" in text_upper:
        credit = max(numbers)

    elif "DR" in text_upper:
        debit = max(numbers)

    # Case 2: Standard format (Withdrawal Deposit Balance)
    elif len(numbers) >= 3:
        txn_amount = numbers[-2]
        balance = numbers[-1]

        if txn_amount < balance:
            credit = txn_amount
        else:
            debit = txn_amount

    # Case 3: Only 2 numbers
    elif len(numbers) == 2:
        amount = numbers[0]
        balance = numbers[1]

        if amount < balance:
            credit = amount
        else:
            debit = amount

    return round(credit, 2), round(debit, 2)


# ===============================
# CSV / EXCEL NORMALIZER
# ===============================
def normalize_dataframe(df):

    df.columns = [c.strip().lower() for c in df.columns]

    transactions = []

    for _, row in df.iterrows():

        credit = float(row.get("credit", 0) or 0)
        debit = float(row.get("debit", 0) or 0)

        transactions.append({
            "date": row.get("date"),
            "credit": round(credit, 2),
            "debit": round(debit, 2),
            "desc": row.get("desc", ""),
            "account": row.get("account", "Uploaded Account")
        })

    return transactions
