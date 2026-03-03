# services/banking_parser.py

import pandas as pd
import pdfplumber
import camelot
import tempfile
from io import BytesIO
import re


# =========================================
# MAIN ENTRY
# =========================================

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


# =========================================
# PDF PARSER
# =========================================

def parse_pdf(file_bytes):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    transactions = []

    try:
        tables = camelot.read_pdf(tmp_path, pages="all", flavor="stream")

        for table in tables:
            df = table.df.replace("\n", " ", regex=True)
            parsed = parse_table_dataframe(df)
            transactions.extend(parsed)

        if transactions:
            return transactions

    except Exception:
        pass

    # Fallback
    return parse_pdf_text(file_bytes)


# =========================================
# TABLE PARSER (COLUMN MAPPED – PRODUCTION SAFE)
# =========================================

def parse_table_dataframe(df):

    transactions = []

    # Convert first row to lowercase header
    header = df.iloc[0].astype(str).str.lower().tolist()

    debit_col = None
    credit_col = None
    balance_col = None
    date_col = None

    for i, col in enumerate(header):

        if "date" in col:
            date_col = i

        if "debit" in col or "withdrawal" in col:
            debit_col = i

        if "credit" in col or "deposit" in col:
            credit_col = i

        if "balance" in col:
            balance_col = i

    # If no header detected, fallback to numeric heuristic
    if debit_col is None and credit_col is None:
        return parse_table_numeric_fallback(df)

    # Skip header row
    for idx in range(1, len(df)):

        row = df.iloc[idx].astype(str).tolist()

        date = None

        if date_col is not None:
            date = row[date_col]
        else:
            date = extract_date_from_row(row)

        if not date or not re.search(r"\d{2}/\d{2}/\d{2}", date):
            continue

        debit = safe_float(row[debit_col]) if debit_col is not None else 0
        credit = safe_float(row[credit_col]) if credit_col is not None else 0
        balance = safe_float(row[balance_col]) if balance_col is not None else 0

        if debit == 0 and credit == 0:
            continue

        transactions.append({
            "date": date,
            "credit": round(credit, 2),
            "debit": round(debit, 2),
            "balance": round(balance, 2),
            "description": " ".join(row)
        })

    return transactions


# =========================================
# NUMERIC FALLBACK (WHEN HEADER NOT FOUND)
# =========================================

def parse_table_numeric_fallback(df):

    transactions = []

    for _, row in df.iterrows():

        row_values = row.astype(str).tolist()
        date = extract_date_from_row(row_values)

        if not date:
            continue

        numbers = extract_money_values(" ".join(row_values))

        if len(numbers) < 2:
            continue

        # Assume: debit | credit | balance
        if len(numbers) >= 3:
            debit = numbers[-3]
            credit = numbers[-2]
            balance = numbers[-1]
        else:
            debit = 0
            credit = numbers[-2]
            balance = numbers[-1]

        if debit == 0 and credit == 0:
            continue

        transactions.append({
            "date": date,
            "credit": round(credit, 2),
            "debit": round(debit, 2),
            "balance": round(balance, 2),
            "description": " ".join(row_values)
        })

    return transactions


# =========================================
# TEXT FALLBACK PARSER
# =========================================

def parse_pdf_text(file_bytes):

    text_data = ""

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_data += page.extract_text() or ""

    lines = text_data.split("\n")
    transactions = []

    for line in lines:

        date_match = re.search(r"\d{2}/\d{2}/\d{2}", line)
        if not date_match:
            continue

        date = date_match.group()
        numbers = extract_money_values(line)

        if len(numbers) < 2:
            continue

        txn_amount = numbers[-2]
        balance = numbers[-1]

        credit = 0
        debit = 0

        if "cr" in line.lower():
            credit = txn_amount
        elif "dr" in line.lower():
            debit = txn_amount
        else:
            # Compare with balance
            if txn_amount < balance:
                credit = txn_amount
            else:
                debit = txn_amount

        transactions.append({
            "date": date,
            "credit": round(credit, 2),
            "debit": round(debit, 2),
            "balance": round(balance, 2),
            "description": line.strip()
        })

    return transactions


# =========================================
# CSV / EXCEL NORMALIZATION
# =========================================

def normalize_dataframe(df):

    df.columns = [c.strip().lower() for c in df.columns]

    transactions = []

    for _, row in df.iterrows():

        credit = safe_float(row.get("credit", 0))
        debit = safe_float(row.get("debit", 0))
        balance = safe_float(row.get("balance", 0))

        transactions.append({
            "date": str(row.get("date")),
            "credit": round(credit, 2),
            "debit": round(debit, 2),
            "balance": round(balance, 2),
            "description": str(row.get("description", ""))
        })

    return transactions


# =========================================
# HELPERS
# =========================================

def extract_date_from_row(values):

    for v in values:
        match = re.search(r"\d{2}/\d{2}/\d{2}", v)
        if match:
            return match.group()

    return None


def extract_money_values(text):

    matches = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", text)

    values = []
    for m in matches:
        try:
            val = float(m.replace(",", ""))
            if val < 10_000_000:
                values.append(val)
        except:
            continue

    return values


def safe_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except:
        return 0
