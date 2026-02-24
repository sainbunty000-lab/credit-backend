import pandas as pd
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
from services.accounting_dictionary import ACCOUNTING_KEYWORDS


def parse_financial_file(file, filename):

    file_bytes = file.read()
    filename = filename.lower()

    result = {}

    # -----------------------------
    # CSV / Excel
    # -----------------------------
    if filename.endswith(".csv"):
        df = pd.read_csv(pd.io.common.BytesIO(file_bytes))

    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(pd.io.common.BytesIO(file_bytes))

    # -----------------------------
    # PDF (Text-Based)
    # -----------------------------
    elif filename.endswith(".pdf"):

        try:
            text = ""

            with pdfplumber.open(pd.io.common.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

            # If text is empty → OCR fallback
            if not text.strip():
                images = convert_from_bytes(file_bytes)
                for img in images:
                    text += pytesseract.image_to_string(img)

        except Exception:
            # OCR direct fallback
            images = convert_from_bytes(file_bytes)
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img)

        lines = text.split("\n")

        for line in lines:
            line_lower = line.lower().replace(",", "")

            for key, words in ACCOUNTING_KEYWORDS.items():
                for word in words:
                    if word in line_lower:
                        numbers = [
                            float(s)
                            for s in line_lower.split()
                            if s.replace(".", "", 1).isdigit()
                        ]
                        if numbers:
                            result[key] = numbers[-1]

        return result

    else:
        raise ValueError("Unsupported file type")

    # -----------------------------
    # CSV / Excel parsing
    # -----------------------------
    for _, row in df.iterrows():
        row_text = " ".join(str(v).lower() for v in row.values)

        for key, words in ACCOUNTING_KEYWORDS.items():
            for word in words:
                if word in row_text:
                    numbers = [
                        float(str(v))
                        for v in row.values
                        if str(v).replace(".", "", 1).isdigit()
                    ]
                    if numbers:
                        result[key] = numbers[-1]

    return result
