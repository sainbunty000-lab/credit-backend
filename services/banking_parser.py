import pandas as pd
import pdfplumber
import pytesseract

from pdf2image import convert_from_bytes
from io import BytesIO


# ==========================================
# MAIN PARSER
# ==========================================
def parse_banking_file(file, filename):

    try:
        file_bytes = file.read()
    except Exception:
        file_bytes = file

    filename = filename.lower()

    # ===============================
    # CSV
    # ===============================
    if filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
        return normalize_dataframe(df)

    # ===============================
    # XLSX
    # ===============================
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
        return normalize_dataframe(df)

    # ===============================
    # XLS
    # ===============================
    elif filename.endswith(".xls"):
        df = pd.read_excel(BytesIO(file_bytes), engine="xlrd")
        return normalize_dataframe(df)

    # ===============================
    # PDF
    # ===============================
    elif filename.endswith(".pdf"):
        return parse_pdf(file_bytes)

    else:
        raise ValueError("Unsupported file format")


# ==========================================
# PDF PARSER (Text + OCR Fallback)
# ==========================================
def parse_pdf(file_bytes):

    text_data = ""

    # Try normal text extraction first
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text_data += page.extract_text() or ""
    except Exception:
        pass

    # If empty → OCR fallback
    if not text_data.strip():
        images = convert_from_bytes(file_bytes)
        for img in images:
            text_data += pytesseract.image_to_string(img)

    return extract_transactions_from_text(text_data)


# ==========================================
# TEXT → TRANSACTIONS
# ==========================================
def extract_transactions_from_text(text):

    lines = text.split("\n")
    transactions = []

    for line in lines:
        parts = line.split()

        # Very basic pattern detection:
        # Date Credit Debit
        if len(parts) >= 3:
            try:
                date = parts[0]
                credit = float(parts[-2].replace(",", ""))
                debit = float(parts[-1].replace(",", ""))

                transactions.append({
                    "date": date,
                    "credit": credit,
                    "debit": debit,
                    "desc": " ".join(parts[1:-2]),
                    "account": "PDF Account"
                })
            except:
                continue

    return transactions


# ==========================================
# NORMALIZE CSV/XLSX
# ==========================================
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
