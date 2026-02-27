import pandas as pd
import pdfplumber
import camelot
import tempfile
import re
from io import BytesIO
from datetime import datetime


# ===============================
# PUBLIC ENTRY
# ===============================
def parse_banking_file(file_bytes, filename):

    filename = filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
        return normalize_dataframe(df)

    if filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(file_bytes))
        return normalize_dataframe(df)

    if filename.endswith(".pdf"):
        return parse_pdf(file_bytes)

    raise ValueError("Unsupported file format")


# ===============================
# PDF PARSER
# ===============================
def parse_pdf(file_bytes):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        tables = camelot.read_pdf(tmp_path, pages="all", flavor="stream")

        if tables:
            all_txns = []
            for table in tables:
                df = table.df
                all_txns.extend(parse_table(df))

            if all_txns:
                return all_txns

    except:
        pass

    return parse_pdf_text(file_bytes)


# ===============================
# TABLE PARSER
# ===============================
def parse_table(df):

    transactions = []
    df = df.replace("\n", " ", regex=True)

    for _, row in df.iterrows():

        row_text = " ".join(row.astype(str).tolist())

        date = extract_date(row_text)
        if not date:
            continue

        credit, debit = extract_amounts(row_text)

        if credit == 0 and debit == 0:
            continue

        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "description": row_text.strip()
        })

    return transactions


# ===============================
# FALLBACK TEXT PARSER
# ===============================
def parse_pdf_text(file_bytes):

    transactions = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = text.split("\n")

            for line in lines:
                date = extract_date(line)
                if not date:
                    continue

                credit, debit = extract_amounts(line)

                if credit == 0 and debit == 0:
                    continue

                transactions.append({
                    "date": date,
                    "credit": credit,
                    "debit": debit,
                    "description": line.strip()
                })

    return transactions


# ===============================
# DATE EXTRACTOR
# ===============================
def extract_date(text):

    patterns = [
        r"\d{2}/\d{2}/\d{4}",
        r"\d{2}/\d{2}/\d{2}",
        r"\d{4}-\d{2}-\d{2}"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                raw = match.group()

                if "/" in raw and len(raw) == 8:
                    dt = datetime.strptime(raw, "%d/%m/%y")
                elif "/" in raw:
                    dt = datetime.strptime(raw, "%d/%m/%Y")
                else:
                    dt = datetime.strptime(raw, "%Y-%m-%d")

                return dt.strftime("%Y-%m-%d")

            except:
                continue

    return None


# ===============================
# AMOUNT EXTRACTION (STRICT)
# ===============================
def extract_amounts(text):

    text_upper = text.upper()

    numbers = []
    for token in text.split():
        cleaned = token.replace(",", "")
        try:
            numbers.append(float(cleaned))
        except:
            continue

    if len(numbers) < 1:
        return 0.0, 0.0

    txn_amount = numbers[-2] if len(numbers) >= 2 else numbers[0]

    credit = 0.0
    debit = 0.0

    if "CR" in text_upper:
        credit = txn_amount
    elif "DR" in text_upper:
        debit = txn_amount
    elif any(x in text_upper for x in ["ATM", "POS", "WITHDRAW", "DEBIT"]):
        debit = txn_amount
    else:
        credit = txn_amount

    return round(credit, 2), round(debit, 2)


# ===============================
# CSV / EXCEL
# ===============================
def normalize_dataframe(df):

    df.columns = [c.lower().strip() for c in df.columns]
    transactions = []

    for _, row in df.iterrows():

        transactions.append({
            "date": str(row.get("date")),
            "credit": float(row.get("credit", 0) or 0),
            "debit": float(row.get("debit", 0) or 0),
            "description": str(row.get("description", ""))
        })

    return transactions
