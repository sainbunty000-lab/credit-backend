import pandas as pd
import pdfplumber
import camelot
import tempfile
import re
from io import BytesIO

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
        if tables and len(tables) > 0:
            all_data = []
            for table in tables:
                all_data.extend(parse_table_dataframe(table.df))
            if all_data: return all_data
    except Exception:
        pass
    return parse_pdf_text(file_bytes)

def parse_table_dataframe(df):
    df = df.replace("\n", " ", regex=True)
    transactions = []
    date_pattern = r"\d{2}/\d{2}/\d{2}"
    for _, row in df.iterrows():
        row_text = " ".join(row.astype(str).tolist())
        if not re.search(date_pattern, row_text): continue
        date = re.search(date_pattern, row_text).group()
        numbers = extract_numbers(row_text)
        if not numbers: continue
        credit, debit = detect_credit_debit(row_text, numbers)
        
        # FIXED: Schema alignment with analyzer
        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "description": row_text.strip(),
            "type": "credit" if credit > 0 else "debit"
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
        if not re.search(date_pattern, line): continue
        date = re.search(date_pattern, line).group()
        numbers = extract_numbers(line)
        if not numbers: continue
        credit, debit = detect_credit_debit(line, numbers)
        
        # FIXED: Schema alignment with analyzer
        transactions.append({
            "date": date,
            "credit": credit,
            "debit": debit,
            "description": line.strip(),
            "type": "credit" if credit > 0 else "debit"
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
    credit, debit = 0.0, 0.0
    text_upper = text.upper()
    if "CR" in text_upper: credit = max(numbers)
    elif "DR" in text_upper: debit = max(numbers)
    elif len(numbers) >= 3:
        txn_amount, balance = numbers[-2], numbers[-1]
        if txn_amount < balance: credit = txn_amount
        else: debit = txn_amount
    elif len(numbers) == 2:
        amount, balance = numbers[0], numbers[1]
        if amount < balance: credit = amount
        else: debit = amount
    return round(credit, 2), round(debit, 2)

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
            "description": row.get("desc", row.get("description", "")),
            "type": "credit" if credit > 0 else "debit"
        })
    return transactions
    
