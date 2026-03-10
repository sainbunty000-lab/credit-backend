import pandas as pd
import pdfplumber
import pytesseract
import re

from pdf2image import convert_from_bytes
from PIL import Image
from io import BytesIO
from docx import Document
from difflib import SequenceMatcher

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

    elif filename.endswith(".docx"):

        text = extract_docx_text(file_bytes)
        extracted = extract_from_text(text)

    elif filename.endswith((".jpg",".jpeg",".png")):

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
# FUZZY MATCH
# ==========================================================

def fuzzy_match(keyword, text, threshold=0.75):

    keyword = keyword.lower()
    text = text.lower()

    ratio = SequenceMatcher(None, keyword, text).ratio()

    return ratio >= threshold


# ==========================================================
# PDF TEXT
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
# OCR PDF
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
# WORD TEXT
# ==========================================================

def extract_docx_text(file_bytes):

    text = ""

    try:

        doc = Document(BytesIO(file_bytes))

        for para in doc.paragraphs:
            text += para.text + "\n"

    except:
        pass

    return text


# ==========================================================
# UNIT DETECTION
# ==========================================================

def detect_multiplier(text):

    text = text.lower()

    if "thousand" in text:
        return 1000

    if "lakh" in text or "lakhs" in text:
        return 100000

    if "crore" in text or "crores" in text:
        return 10000000

    if "million" in text:
        return 1000000

    return 1


# ==========================================================
# DATAFRAME EXTRACTION
# ==========================================================

def extract_from_dataframe(df):

    result = {}

    text_blob = " ".join(df.astype(str).values.flatten())

    multiplier = detect_multiplier(text_blob)

    for _, row in df.iterrows():

        row_text = " ".join(str(v).lower() for v in row.values)

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            if key in result:
                continue

            for keyword in keywords:

                if keyword in row_text or fuzzy_match(keyword, row_text):

                    numbers = extract_numbers(row.values)

                    if numbers:

                        value = pick_latest_value(numbers) * multiplier

                        if abs(value) > 100:
                            result[key] = value

    return result


# ==========================================================
# TEXT EXTRACTION
# ==========================================================

def extract_from_text(text):

    result = {}

    multiplier = detect_multiplier(text)

    lines = text.split("\n")

    prev_line = ""

    for line in lines:

        clean_line = line.lower()

        combined_line = prev_line + " " + clean_line

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            if key in result:
                continue

            for keyword in keywords:

                if keyword in combined_line or fuzzy_match(keyword, combined_line):

                    numbers = extract_numbers([combined_line])

                    if numbers:

                        value = pick_latest_value(numbers) * multiplier

                        if abs(value) > 100:
                            result[key] = value

        prev_line = clean_line

    return result


# ==========================================================
# NUMBER EXTRACTION
# ==========================================================

def extract_numbers(values):

    numbers = []

    for v in values:

        text = str(v)

        text = text.replace("₹","")

        matches = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text)

        for m in matches:

            m = m.replace(",", "")

            try:
                numbers.append(float(m))
            except:
                pass

    return numbers


# ==========================================================
# LATEST YEAR DETECTION
# ==========================================================

def pick_latest_value(numbers):

    if len(numbers) >= 2:
        return numbers[-2]

    return numbers[-1]


# ==========================================================
# CAM FINANCIAL CALCULATIONS
# ==========================================================

def calculate_financial_metrics(data):

    sales = data.get("sales",0)
    other_income = data.get("other_income",0)
    expenses = data.get("total_expenses",0)
    interest = data.get("interest",0)
    depreciation = data.get("depreciation",0)
    tax = data.get("tax",0)

    equity = data.get("equity_share_capital",0)
    reserves = data.get("reserves",0)

    short_debt = data.get("short_term_debt",0)
    long_debt = data.get("long_term_debt",0)
    unsecured = data.get("unsecured_loans",0)

    current_assets = data.get("current_assets",0)
    current_liabilities = data.get("current_liabilities",0)

    total_income = sales + other_income
    pbdt = total_income - expenses
    pbt = pbdt - interest - depreciation
    pat = pbt - tax
    cash_profit = pat + depreciation

    networth = equity + reserves
    total_debt = short_debt + long_debt + unsecured

    current_ratio = current_assets / current_liabilities if current_liabilities else 0
    debt_equity = total_debt / networth if networth else 0
    net_margin = pat / sales if sales else 0

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
