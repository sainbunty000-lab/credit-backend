import pdfplumber
import pandas as pd
from io import BytesIO
import re


# =====================================================
# MAIN ENTRY
# =====================================================
def parse_banking_file(file_bytes, filename):

    filename = filename.lower()

    if filename.endswith(".pdf"):
        return parse_pdf(file_bytes)

    elif filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
        return normalize_dataframe(df)

    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(BytesIO(file_bytes))
        return normalize_dataframe(df)

    else:
        raise ValueError("Unsupported file format")


# =====================================================
# PDF PARSER (TABLE BASED)
# =====================================================
def parse_pdf(file_bytes):

    transactions = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:

                if not table or len(table) < 2:
                    continue

                headers = [str(h).lower() if h else "" for h in table[0]]

                # Try to detect column positions
                date_index = find_column(headers, ["date"])
                debit_index = find_column(headers, ["debit", "withdrawal", "dr"])
                credit_index = find_column(headers, ["credit", "deposit", "cr"])
                balance_index = find_column(headers, ["balance"])

                if date_index is None:
                    continue

                for row in table[1:]:

                    try:
                        date_val = row[date_index]
                        if not date_val:
                            continue

                        if not re.search(r"\d{2}/\d{2}/\d{2}", str(date_val)):
                            continue

                        debit = safe_float(row[debit_index]) if debit_index is not None else 0
                        credit = safe_float(row[credit_index]) if credit_index is not None else 0

                        # Skip empty rows
                        if debit == 0 and credit == 0:
                            continue

                        transactions.append({
                            "date": str(date_val),
                            "debit": debit,
                            "credit": credit,
                            "description": " ".join(str(c) for c in row if c)
                        })

                    except Exception:
                        continue

    return transactions


# =====================================================
# HELPER FUNCTIONS
# =====================================================
def find_column(headers, keywords):

    for i, header in enumerate(headers):
        for keyword in keywords:
            if keyword in header:
                return i

    return None


def normalize_dataframe(df):

    df.columns = [c.lower().strip() for c in df.columns]

    transactions = []

    for _, row in df.iterrows():

        credit = safe_float(row.get("credit", 0))
        debit = safe_float(row.get("debit", 0))

        if debit == 0 and credit == 0:
            continue

        transactions.append({
            "date": str(row.get("date")),
            "credit": credit,
            "debit": debit,
            "description": str(row.get("description", "")),
        })

    return transactions


def safe_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except:
        return 0
