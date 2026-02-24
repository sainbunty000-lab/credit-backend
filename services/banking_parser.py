import pandas as pd
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
from datetime import datetime


# ======================================================
# MAIN ENTRY FUNCTION
# ======================================================
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
    # PDF (Text + OCR Fallback)
    # ===============================
    elif filename.endswith(".pdf"):

        text = ""

        # Try text-based extraction
        try:
            with pdfplumber.open(BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted
        except Exception:
            pass

        # OCR fallback
        if not text.strip():
            images = convert_from_bytes(file_bytes)
            for img in images:
                text += pytesseract.image_to_string(img)

        if not text.strip():
            raise ValueError("Unable to extract transactions from PDF")

        return extract_transactions_from_text(text)

    else:
       
