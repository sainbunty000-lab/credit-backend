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
                text += page.extract_text() + "\n"

        lines = text.split("\n")
        data = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                label = " ".join(parts[:-1])
                try:
                    value = float(parts[-1].replace(",", ""))
                    data.append({"label": label, "value": value})
                except:
                    continue
        df = pd.DataFrame(data)
    else:
        raise ValueError("Unsupported format")

    result = {}
    for _, row in df.iterrows():
        label = str(row[0])
        value = float(row[1])
        matched = match_keywords(label)
        if matched:
            result[matched] = value

    return result
