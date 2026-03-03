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
        return 0    return parse_with_pdfplumber(file_bytes)


# =========================================
# CAMEL0T TABLE EXTRACTION
# =========================================

def extract_from_camelot_tables(tables):

    transactions = []

    for table in tables:
        df = table.df.replace("\n", " ", regex=True)

        parsed = parse_table_dataframe(df)
        transactions.extend(parsed)

    return transactions


# =========================================
# COLUMN-BASED TABLE PARSER
# =========================================

def parse_table_dataframe(df):

    transactions = []

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

    # If required columns missing → skip this table
    if debit_col is None or credit_col is None:
        return []

    for idx in range(1, len(df)):

        row = df.iloc[idx].astype(str).tolist()

        date = row[date_col] if date_col is not None else None

        # STRICT DATE VALIDATION
        if not date or not re.fullmatch(r"\d{2}/\d{2}/\d{2}", date.strip()):
            continue

        debit = safe_float(row[debit_col])
        credit = safe_float(row[credit_col])
        balance = safe_float(row[balance_col]) if balance_col else 0

        # Strict validation rules
        if debit > 0 and credit > 0:
            continue

        if debit == 0 and credit == 0:
            continue

        transactions.append({
            "date": date.strip(),
            "credit": round(credit, 2),
            "debit": round(debit, 2),
            "balance": round(balance, 2),
            "description": " ".join(row)
        })

    return transactions


# =========================================
# PDFPLUMBER STRUCTURED FALLBACK
# =========================================

def parse_with_pdfplumber(file_bytes):

    transactions = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:

                if not table or len(table) < 2:
                    continue

                header = [str(h).lower() if h else "" for h in table[0]]

                debit_col = None
                credit_col = None
                balance_col = None
                date_col = None

                for i, col in enumerate(header):

                    if "date" in col:
                        date_col = i
                    if "debit" in col:
                        debit_col = i
                    if "credit" in col:
                        credit_col = i
                    if "balance" in col:
                        balance_col = i

                if debit_col is None or credit_col is None:
                    continue

                for row in table[1:]:

                    if not row:
                        continue

                    row = [str(r) if r else "" for r in row]

                    date = row[date_col] if date_col is not None else None

                    if not date or not re.fullmatch(r"\d{2}/\d{2}/\d{2}", date.strip()):
                        continue

                    debit = safe_float(row[debit_col])
                    credit = safe_float(row[credit_col])
                    balance = safe_float(row[balance_col]) if balance_col else 0

                    if debit > 0 and credit > 0:
                        continue

                    if debit == 0 and credit == 0:
                        continue

                    transactions.append({
                        "date": date.strip(),
                        "credit": round(credit, 2),
                        "debit": round(debit, 2),
                        "balance": round(balance, 2),
                        "description": " ".join(row)
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
# SAFE FLOAT
# =========================================

def safe_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except:
        return 0
