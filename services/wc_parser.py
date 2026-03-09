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

    try:
        file_bytes = file.read()
    except:
        file_bytes = file

    filename = filename.lower()

    # ======================================
    # CSV
    # ======================================
    if filename.endswith(".csv"):

        df = pd.read_csv(BytesIO(file_bytes))
        return extract_from_dataframe(df)

    # ======================================
    # XLSX
    # ======================================
    elif filename.endswith(".xlsx"):

        df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
        return extract_from_dataframe(df)

    # ======================================
    # XLS
    # ======================================
    elif filename.endswith(".xls"):

        df = pd.read_excel(BytesIO(file_bytes), engine="xlrd")
        return extract_from_dataframe(df)

    # ======================================
    # PDF
    # ======================================
    elif filename.endswith(".pdf"):

        text = extract_pdf_text(file_bytes)

        # If no text → scanned PDF
        if not text.strip():
            text = extract_pdf_ocr(file_bytes)

        return extract_from_text(text)

    # ======================================
    # IMAGE (JPG / PNG)
    # ======================================
    elif filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):

        text = extract_image_ocr(file_bytes)

        return extract_from_text(text)

    else:
        raise ValueError("Unsupported file type")


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
# OCR EXTRACTION (SCANNED PDF)
# ==========================================================

def extract_pdf_ocr(file_bytes):

    text = ""

    images = convert_from_bytes(file_bytes)

    for img in images:

        ocr_text = pytesseract.image_to_string(img)

        text += ocr_text + "\n"

    return text


# ==========================================================
# OCR EXTRACTION (IMAGE)
# ==========================================================

def extract_image_ocr(file_bytes):

    text = ""

    try:

        image = Image.open(BytesIO(file_bytes))

        text = pytesseract.image_to_string(image)

    except:
        pass

    return text


# ==========================================================
# EXTRACT FROM DATAFRAME
# ==========================================================

def extract_from_dataframe(df):

    result = {}

    for _, row in df.iterrows():

        row_text = " ".join(str(v).lower() for v in row.values)
        normalized_row = row_text.replace(" ", "")

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            for keyword in keywords:

                keyword_norm = keyword.lower().replace(" ", "")

                if keyword_norm in normalized_row:

                    numbers = extract_numbers(row.values)

                    if numbers:
                        result[key] = numbers[-1]

    return result


# ==========================================================
# EXTRACT FROM TEXT
# ==========================================================

def extract_from_text(text):

    result = {}

    lines = text.split("\n")

    for line in lines:

        clean_line = line.lower().replace(",", "")
        normalized_line = clean_line.replace(" ", "")

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            for keyword in keywords:

                keyword_norm = keyword.lower().replace(" ", "")

                if keyword_norm in normalized_line:

                    numbers = extract_numbers([line])

                    if numbers:
                        result[key] = numbers[-1]

    return result


# ==========================================================
# NUMBER EXTRACTION
# ==========================================================

def extract_numbers(values):

    numbers = []

    for v in values:

        text = str(v)

        text = text.replace(",", "")

        matches = re.findall(r"-?\d+\.?\d*", text)

        for m in matches:

            try:
                numbers.append(float(m))
            except:
                pass

    return numbers
