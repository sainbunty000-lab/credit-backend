import pandas as pd
import pdfplumber
import pytesseract
import re

from pdf2image import convert_from_bytes
from PIL import Image
from io import BytesIO

from services.accounting_dictionary import ACCOUNTING_KEYWORDS


# ==========================================================
# MAIN ENTRY
# ==========================================================

def parse_financial_file(file, filename):

    if isinstance(file, bytes):
        file_bytes = file
    else:
        file_bytes = file.read()

    filename = filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
        extracted = extract_from_dataframe(df)

    elif filename.endswith(".xlsx"):
        df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
        extracted = extract_from_dataframe(df)

    elif filename.endswith(".xls"):
        df = pd.read_excel(BytesIO(file_bytes), engine="xlrd")
        extracted = extract_from_dataframe(df)

    elif filename.endswith(".pdf"):

        text = extract_pdf_text(file_bytes)

        if not text.strip():
            text = extract_pdf_ocr(file_bytes)

        extracted = extract_from_text(text)

    elif filename.endswith((".jpg", ".jpeg", ".png")):

        text = extract_image_ocr(file_bytes)

        extracted = extract_from_text(text)

    else:
        raise ValueError("Unsupported file type")

    calculations = calculate_financial_metrics(extracted)

    return {
        "inputs": extracted,
        "calculations": calculations
    }


# ==========================================================
# PDF TEXT EXTRACTION
# ==========================================================

def extract_pdf_text(file_bytes):

    text = ""

    try:

        with pdfplumber.open(BytesIO(file_bytes)) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

    except:
        pass

    return text


# ==========================================================
# OCR FOR SCANNED PDF
# ==========================================================

def extract_pdf_ocr(file_bytes):

    text = ""

    images = convert_from_bytes(file_bytes)

    for img in images:

        ocr_text = pytesseract.image_to_string(img, config="--psm 6")

        text += ocr_text + "\n"

    return text


# ==========================================================
# OCR IMAGE
# ==========================================================

def extract_image_ocr(file_bytes):

    try:

        image = Image.open(BytesIO(file_bytes))

        text = pytesseract.image_to_string(image, config="--psm 6")

        return text

    except:
        return ""


# ==========================================================
# DETECT UNIT SCALE
# ==========================================================

def detect_multiplier(text):

    text = text.lower()

    if "in thousand" in text:
        return 1000

    if "in lakh" in text or "in lakhs" in text:
        return 100000

    if "in crore" in text or "in crores" in text:
        return 10000000

    if "in million" in text:
        return 1000000

    return 1


# ==========================================================
# EXTRACT FROM DATAFRAME
# ==========================================================

def extract_from_dataframe(df):

    result = {}

    text_blob = " ".join(df.astype(str).values.flatten())

    multiplier = detect_multiplier(text_blob)

    for _, row in df.iterrows():

        row_text = " ".join(str(v).lower() for v in row.values)

        normalized_row = row_text.replace(" ", "").replace(",", "")

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            if key in result:
                continue

            for keyword in keywords:

                keyword_norm = keyword.lower().replace(" ", "")

                if keyword_norm in normalized_row:

                    numbers = extract_numbers(row.values)

                    if numbers:

                        value = numbers[-1] * multiplier

                        if abs(value) > 100:
                            result[key] = value

    return result


# ==========================================================
# EXTRACT FROM TEXT
# ==========================================================

def extract_from_text(text):

    result = {}

    multiplier = detect_multiplier(text)

    lines = text.split("\n")

    for line in lines:

        clean_line = line.lower().replace(",", "")

        normalized_line = clean_line.replace(" ", "")

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            if key in result:
                continue

            for keyword in keywords:

                keyword_norm = keyword.lower().replace(" ", "")

                if keyword_norm in normalized_line:

                    numbers = extract_numbers([line])

                    if numbers:

                        value = numbers[-1] * multiplier

                        if abs(value) > 100:
                            result[key] = value

    return result


# ==========================================================
# NUMBER EXTRACTION
# ==========================================================

def extract_numbers(values):

    numbers = []

    for v in values:

        text = str(v)

        text = text.replace(",", "").replace("₹", "")

        matches = re.findall(r"\(?-?\d+(?:\.\d+)?\)?", text)

        for m in matches:

            m = m.replace("(", "-").replace(")", "")

            try:
                numbers.append(float(m))
            except:
                pass

    return numbers


# ==========================================================
# SAFE DIVIDE
# ==========================================================

def safe_divide(a, b):

    if b == 0:
        return 0

    return a / b


# ==========================================================
# CAM FINANCIAL CALCULATIONS
# ==========================================================

def calculate_financial_metrics(data):

    sales = data.get("sales", 0)
    other_income = data.get("other_income", 0)
    expenses = data.get("total_expenses", 0)
    interest = data.get("interest", 0)
    depreciation = data.get("depreciation", 0)
    tax = data.get("tax", 0)

    equity = data.get("equity_share_capital", 0)
    reserves = data.get("reserves", 0)

    short_debt = data.get("short_term_debt", 0)
    long_debt = data.get("long_term_debt", 0)
    unsecured = data.get("unsecured_loans", 0)

    current_assets = data.get("current_assets", 0)
    current_liabilities = data.get("current_liabilities", 0)

    # =====================================
    # PROFIT CALCULATIONS
    # =====================================

    total_income = sales + other_income

    pbdt = total_income - expenses

    pbt = pbdt - interest - depreciation

    pat = pbt - tax

    cash_profit = pat + depreciation

    # =====================================
    # NET WORTH
    # =====================================

    networth = equity + reserves

    # =====================================
    # TOTAL DEBT
    # =====================================

    total_debt = short_debt + long_debt + unsecured

    # =====================================
    # RATIOS
    # =====================================

    current_ratio = safe_divide(current_assets, current_liabilities)

    debt_equity = safe_divide(total_debt, networth)

    net_margin = safe_divide(pat, sales)

    return {
        "total_income": total_income,
        "pbdt": pbdt,
        "pbt": pbt,
        "pat": pat,
        "cash_profit": cash_profit,
        "networth": networth,
        "total_debt": total_debt,
        "current_ratio": current_ratio,
        "debt_equity": debt_equity,
        "net_margin": net_margin
    }
