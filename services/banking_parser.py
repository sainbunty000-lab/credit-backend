# services/banking_parser.py

import pandas as pd
import pdfplumber
import camelot
import tempfile
from io import BytesIO
import re


# ==============================
# MAIN PARSER ENTRY
# ==============================

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


# ==============================
# PDF PARSER
# ==============================

def parse_pdf(file_bytes):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        tables = camelot.read_pdf(tmp_path, pages="all", flavor="stream")

        transactions = []

        for table in tables:
            df = table.df
            df = df.replace("\n", " ", regex=True)

            parsed = parse_table_dataframe(df)
            transactions.extend(parsed)

        if transactions:
            return transactions

    except Exception:
        pass

    # Fallback text mode
    return parse_pdf_text(file_bytes)


# ==============================
# TABLE DATAFRAME PARSER
# ==============================

def parse_table_dataframe(df):

    transactions = []

    for _, row in df.iterrows():

        row_values = row.astype(str).tolist()

        date = extract_date_from_row(row_values)
        if not date:
            continue

        debit, credit = detect_amount_columns(row_values)

        # Skip invalid rows
        if debit == 0 and credit == 0:
            continue

        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "description": " ".join(row_values),
        })

    return transactions


# ==============================
# TEXT FALLBACK PARSER
# ==============================

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

        # Last two monetary values are usually txn + balance
        txn_amount = numbers[-2]

        if "cr" in line.lower():
            credit = txn_amount
            debit = 0
        elif "dr" in line.lower():
            debit = txn_amount
            credit = 0
        else:
            # Cannot determine safely
            continue

        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "description": line.strip()
        })

    return transactions


# ==============================
# HELPERS
# ==============================

def normalize_dataframe(df):

    df.columns = [c.strip().lower() for c in df.columns]

    transactions = []

    for _, row in df.iterrows():

        credit = safe_float(row.get("credit", 0))
        debit = safe_float(row.get("debit", 0))

        # Sanity check
        if credit > 10_000_000:
            credit = 0

        transactions.append({
            "date": str(row.get("date")),
            "credit": credit,
            "debit": debit,
            "description": str(row.get("description", "")),
        })

    return transactions


def extract_date_from_row(values):

    for v in values:
        match = re.search(r"\d{2}/\d{2}/\d{2}", v)
        if match:
            return match.group()

    return None


def detect_amount_columns(values):

    money_values = []

    for v in values:
        cleaned = v.replace(",", "").strip()
        try:
            val = float(cleaned)
            if 0 < val < 10_000_000:  # sanity range
                money_values.append(val)
        except:
            continue

    if len(money_values) < 2:
        return 0, 0

    txn_amount = money_values[-2]

    # Try heuristic: negative numbers = debit
    if txn_amount < 0:
        return abs(txn_amount), 0

    return 0, txn_amount


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
