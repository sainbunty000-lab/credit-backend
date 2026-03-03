# services/banking_parser.py

import pandas as pd
import pdfplumber
import camelot
import tempfile
from io import BytesIO
import re


# ======================================
# MAIN PARSER ENTRY
# ======================================

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


# ======================================
# PDF PARSER
# ======================================

def parse_pdf(file_bytes):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    transactions = []

    try:
        tables = camelot.read_pdf(tmp_path, pages="all", flavor="stream")

        for table in tables:
            df = table.df
            df = df.replace("\n", " ", regex=True)
            parsed = parse_table_dataframe(df)
            transactions.extend(parsed)

        if transactions:
            return transactions

    except Exception:
        pass

    # Fallback to text parsing
    return parse_pdf_text(file_bytes)


# ======================================
# TABLE PARSER (Improved Detection)
# ======================================

def parse_table_dataframe(df):

    transactions = []

    for _, row in df.iterrows():

        row_values = row.astype(str).tolist()

        date = extract_date_from_row(row_values)
        if not date:
            continue

        debit, credit, balance = detect_amount_columns(row_values)

        # Skip invalid rows
        if debit == 0 and credit == 0:
            continue

        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "balance": balance,
            "description": " ".join(row_values),
        })

    return transactions


# ======================================
# TEXT FALLBACK PARSER
# ======================================

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
            # Heuristic: compare with balance
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


# ======================================
# CSV / EXCEL NORMALIZATION
# ======================================

def normalize_dataframe(df):

    df.columns = [c.strip().lower() for c in df.columns]

    transactions = []

    for _, row in df.iterrows():

        credit = safe_float(row.get("credit", 0))
        debit = safe_float(row.get("debit", 0))
        balance = safe_float(row.get("balance", 0))

        transactions.append({
            "date": str(row.get("date")),
            "credit": credit,
            "debit": debit,
            "balance": balance,
            "description": str(row.get("description", "")),
        })

    return transactions


# ======================================
# HELPERS
# ======================================

def extract_date_from_row(values):

    for v in values:
        match = re.search(r"\d{2}/\d{2}/\d{2}", v)
        if match:
            return match.group()

    return None


# 🔥 IMPORTANT FIX: Proper Debit/Credit Detection
def detect_amount_columns(values):

    money_values = []

    for v in values:
        cleaned = v.replace(",", "").strip()
        try:
            val = float(cleaned)
            if 0 < abs(val) < 10_000_000:
                money_values.append(val)
        except:
            continue

    if len(money_values) < 2:
        return 0, 0, None

    # Assume structure: Debit | Credit | Balance
    # Most Indian banks use this format
    if len(money_values) >= 3:
        debit_candidate = money_values[-3]
        credit_candidate = money_values[-2]
        balance = money_values[-1]

        debit = debit_candidate if debit_candidate > 0 else 0
        credit = credit_candidate if credit_candidate > 0 else 0

        # Prevent both filled
        if debit > 0 and credit > 0:
            if debit > credit:
                credit = 0
            else:
                debit = 0

        return round(debit, 2), round(credit, 2), round(balance, 2)

    # If only amount + balance
    txn_amount = money_values[-2]
    balance = money_values[-1]

    debit = 0
    credit = 0

    if txn_amount < balance:
        credit = txn_amount
    else:
        debit = txn_amount

    return round(debit, 2), round(credit, 2), round(balance, 2)


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
        return float(value)
    except:
        return 0
