import pandas as pd
import pdfplumber
from io import BytesIO

def parse_banking_file(file_bytes, filename):

    filename = filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
        return normalize_dataframe(df)

    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(BytesIO(file_bytes))
        return normalize_dataframe(df)

    elif filename.endswith(".pdf"):
        return parse_pdf(file_bytes)

    else:
        raise ValueError("Unsupported file format")


def parse_pdf(file_bytes):

    text_data = ""

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_data += page.extract_text() or ""

    if not text_data.strip():
        raise Exception("Scanned PDF not supported.")

    return extract_transactions_from_text(text_data)


def extract_transactions_from_text(text):

    lines = text.split("\n")
    transactions = []

    for line in lines:
        parts = line.split()

        if len(parts) < 3:
            continue

        date = parts[0]

        numbers = []
        for p in parts:
            try:
                numbers.append(float(p.replace(",", "")))
            except:
                continue

        if numbers:
            credit = numbers[-1]
            debit = numbers[-2] if len(numbers) > 1 else 0

            transactions.append({
                "date": date,
                "credit": credit,
                "debit": debit,
                "desc": line,
                "account": "PDF Account"
            })

    return transactions


def normalize_dataframe(df):

    df.columns = [c.strip().lower() for c in df.columns]

    transactions = []

    for _, row in df.iterrows():
        transactions.append({
            "date": row.get("date"),
            "credit": float(row.get("credit", 0) or 0),
            "debit": float(row.get("debit", 0) or 0),
            "desc": row.get("desc", ""),
            "account": row.get("account", "Uploaded Account")
        })

    return transactions
