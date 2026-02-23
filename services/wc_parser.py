import pandas as pd
import pdfplumber
import re
from utils.safe_math import default_zero

# Global Financial Dictionary
GLOBAL_ACCOUNT_MAP = {
    "current_assets": [
        "current assets", "total current assets",
        "circulating assets"
    ],
    "current_liabilities": [
        "current liabilities", "total current liabilities",
        "short term liabilities"
    ],
    "inventory": [
        "inventory", "inventories", "closing stock", "stock"
    ],
    "trade_receivables": [
        "trade receivables", "accounts receivable",
        "sundry debtors", "debtors"
    ],
    "trade_payables": [
        "trade payables", "accounts payable",
        "sundry creditors", "creditors"
    ],
    "revenue": [
        "revenue", "sales", "turnover", "net sales"
    ],
    "cogs": [
        "cost of goods sold", "cost of sales", "cogs"
    ]
}

def normalize(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())

def extract_value(df, keywords):
    for keyword in keywords:
        match = df[df["label"].str.contains(keyword, na=False)]
        if not match.empty:
            return default_zero(match["value"].values[0])
    return 0.0

def parse_pdf(file):
    rows = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2:
                        label = " ".join(parts[:-1])
                        try:
                            value = float(parts[-1].replace(",", ""))
                            rows.append([label, value])
                        except:
                            continue
    return pd.DataFrame(rows, columns=["label", "value"])

def parse_financial_file(file, filename):

    if filename.endswith(".csv"):
        df = pd.read_csv(file)

    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(file)

    elif filename.endswith(".pdf"):
        df = parse_pdf(file)

    else:
        return {}

    if df.shape[1] < 2:
        return {}

    df.columns = ["label", "value"]
    df["label"] = df["label"].apply(normalize)

    parsed = {}

    for field, keywords in GLOBAL_ACCOUNT_MAP.items():
        parsed[field] = extract_value(df, keywords)

    return parsed
