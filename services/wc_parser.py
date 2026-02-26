import pandas as pd
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
from services.accounting_dictionary import ACCOUNTING_KEYWORDS


# ==========================================================
# MAIN ENTRY FUNCTION
# ==========================================================
def parse_financial_file(file, filename):

    try:
        file_bytes = file.read()
    except Exception:
        file_bytes = file

    filename = filename.lower()

    # ===================================
    # CSV
    # ===================================
    if filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(file_bytes))
        return extract_from_dataframe(df)

    # ===================================
    # XLSX
    # ===================================
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
        return extract_from_dataframe(df)

    # ===================================
    # XLS
    # ===================================
    elif filename.endswith(".xls"):
        df = pd.read_excel(BytesIO(file_bytes), engine="xlrd")
        return extract_from_dataframe(df)

    # ===================================
    # PDF
    # ===================================
    elif filename.endswith(".pdf"):

        text = ""

        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception:
            pass

        # OCR fallback
        if not text.strip():
            images = convert_from_bytes(file_bytes)
            for img in images:
                text += pytesseract.image_to_string(img)

        if not text.strip():
            raise ValueError("No readable text found in PDF")

        return extract_from_text(text)

    else:
        raise ValueError("Unsupported file type")


# ==========================================================
# Extract from Excel / CSV
# ==========================================================
def extract_from_dataframe(df):

    result = {}

    for _, row in df.iterrows():

        row_text = " ".join(str(v).lower() for v in row.values)
        normalized_row = row_text.replace(" ", "")

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            for keyword in keywords:

                normalized_keyword = keyword.lower().replace(" ", "")

                if normalized_keyword in normalized_row:

                    numbers = []

                    for v in row.values:
                        try:
                            clean_val = str(v).replace(",", "")
                            num = float(clean_val)
                            numbers.append(num)
                        except:
                            continue

                    if numbers:
                        result[key] = numbers[-1]

    return result


# ==========================================================
# Extract from PDF Text
# ==========================================================
def extract_from_text(text):

    result = {}
    lines = text.split("\n")

    for line in lines:

        clean_line = line.lower().replace(",", "")
        normalized_line = clean_line.replace(" ", "")

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            for keyword in keywords:

                normalized_keyword = keyword.lower().replace(" ", "")

                if normalized_keyword in normalized_line:

                    numbers = []

                    for word in clean_line.split():
                        try:
                            num = float(word)
                            numbers.append(num)
                        except:
                            continue

                    if numbers:
                        result[key] = numbers[-1]

    return result
