import pandas as pd
import io
import pdfplumber
from services.accounting_dictionary import ACCOUNTING_KEYWORDS

def match_keywords(label):
    label = label.lower()
    for key, words in ACCOUNTING_KEYWORDS.items():
        for w in words:
            if w in label:
                return key
    return None

def parse_financial_file(file_bytes, filename):
    filename = filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(file_bytes))
    elif filename.endswith(".pdf"):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

    if not text:
        raise ValueError("No readable text found in PDF")

    lines = text.split("\n")
    data = []

    for line in lines:
        line_clean = line.lower().replace(",", "")
        for key, words in ACCOUNTING_KEYWORDS.items():
            for w in words:
                if w in line_clean:
                    numbers = [float(s) for s in line_clean.split() if s.replace('.', '', 1).isdigit()]
                    if numbers:
                        data.append({"label": key, "value": numbers[-1]})

    return {item["label"]: item["value"] for item in data}
