import pandas as pd
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
from services.accounting_dictionary import accounting_keywords


def parse_financial_file(file, filename):

    # -----------------------------------
    # Safe file reading (UploadFile / bytes)
    # -----------------------------------
    try:
        file_bytes = file.read()
    except Exception:
        file_bytes = file

    filename = filename.lower()
    result = {}

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

        df = pd.read_excel(
            BytesIO(file_bytes),
            engine="openpyxl"
        )

        return extract_from_dataframe(df)

    # ===================================
    # XLS
    # ===================================
    elif filename.endswith(".xls"):

        df = pd.read_excel(
            BytesIO(file_bytes),
            engine="xlrd"
        )

        return extract_from_dataframe(df)

    # ===================================
    # PDF (Text + OCR fallback)
    # ===================================
    elif filename.endswith(".pdf"):

        text = ""

        # Try text-based extraction first
        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted
        except Exception:
            pass

        # If no text found → OCR fallback
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
# Extract from DataFrame
# ==========================================================
def extract_from_dataframe(df):

    result = {}

    for _, row in df.iterrows():

        row_text = " ".join(str(v).lower() for v in row.values)

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            for keyword in keywords:

                if keyword in row_text:

                    numbers = [
                        float(str(v))
                        for v in row.values
                        if str(v).replace(".", "", 1).isdigit()
                    ]

                    if numbers:
                        result[key] = numbers[-1]

    return result


# ==========================================================
# Extract from raw text (PDF)
# ==========================================================
def extract_from_text(text):

    result = {}
    lines = text.split("\n")

    for line in lines:

        clean_line = line.lower().replace(",", "")

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            for keyword in keywords:

                if keyword in clean_line:

                    numbers = [
                        float(word)
                        for word in clean_line.split()
                        if word.replace(".", "", 1).isdigit()
                    ]

                    if numbers:
                        result[key] = numbers[-1]

    return result
