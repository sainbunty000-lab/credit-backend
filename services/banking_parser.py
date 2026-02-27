import pandas as pd
import pdfplumber
import camelot
import tempfile
import re
from io import BytesIO


def clean_amount(value):
    if value is None:
        return 0.0

    value = str(value).replace(",", "").strip()

    try:
        return float(value)
    except:
        return 0.0


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


def parse_pdf(file_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        tables = camelot.read_pdf(tmp_path, pages="all", flavor="stream")
        if tables:
            all_txn = []
            for table in tables:
                all_txn.extend(parse_table_dataframe(table.df))
            if all_txn:
                return all_txn
    except:
        pass

    return parse_pdf_text(file_bytes)


def parse_table_dataframe(df):
    df = df.replace("\n", " ", regex=True)
    transactions = []

    date_pattern = r"\d{2}/\d{2}/\d{2}"

    for _, row in df.iterrows():
        row_text = " ".join(row.astype(str).tolist())

        if not re.search(date_pattern, row_text):
            continue

        date = re.search(date_pattern, row_text).group()

        numbers = extract_numbers(row_text)
        if len(numbers) < 1:
            continue

        credit, debit = detect_credit_debit(row_text, numbers)

        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "description": row_text.strip()
        })

    return transactions


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

        date = re.search(date_pattern, line).group()

        numbers = extract_numbers(line)
        if len(numbers) < 1:
            continue

        credit, debit = detect_credit_debit(line, numbers)

        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "description": line.strip()
        })

    return transactions


def extract_numbers(text):
    numbers = []

    for token in text.split():
        cleaned = token.replace(",", "")
        try:
            numbers.append(float(cleaned))
        except:
            continue

    return numbers


def detect_credit_debit(text, numbers):
    text_upper = text.upper()

    credit = 0.0
    debit = 0.0

    # Most reliable pattern: amount usually second last, balance last
    if len(numbers) >= 2:
        txn_amount = numbers[-2]
    else:
        txn_amount = numbers[0]

    txn_amount = clean_amount(txn_amount)

    if "CR" in text_upper:
        credit = txn_amount

    elif "DR" in text_upper:
        debit = txn_amount

    else:
        # fallback: detect sign using keywords
        if any(word in text_upper for word in ["WITHDRAW", "ATM", "DEBIT", "POS"]):
            debit = txn_amount
        else:
            credit = txn_amount

    return round(credit, 2), round(debit, 2)


def normalize_dataframe(df):
    df.columns = [c.strip().lower() for c in df.columns]

    transactions = []

    for _, row in df.iterrows():
        credit = clean_amount(row.get("credit", 0))
        debit = clean_amount(row.get("debit", 0))

        transactions.append({
            "date": row.get("date"),
            "credit": round(credit, 2),
            "debit": round(debit, 2),
            "description": row.get("description", "")
        })

    return transactions
