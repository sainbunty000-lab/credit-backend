import pdfplumber
from io import BytesIO
import re


def parse_pdf_text_based(file_bytes):

    transactions = []
    current_month = None

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")

            for line in lines:

                # Skip summary sections
                if "total debit" in line.lower():
                    continue
                if "opening balance" in line.lower():
                    continue

                date_match = re.search(r"\d{2}/\d{2}/\d{2}", line)
                if not date_match:
                    continue

                numbers = extract_money_values(line)

                # Transaction rows usually have 2 or 3 numbers
                if len(numbers) < 2:
                    continue

                debit = 0
                credit = 0

                line_lower = line.lower()

                # Detect DR/CR explicitly
                if "dr" in line_lower:
                    debit = numbers[-2]
                elif "cr" in line_lower:
                    credit = numbers[-2]
                else:
                    # Skip ambiguous rows
                    continue

                # Ignore tiny values that are balance carry forwards
                if debit < 1 and credit < 1:
                    continue

                transactions.append({
                    "date": date_match.group(),
                    "credit": credit,
                    "debit": debit,
                    "description": line.strip()
                })

    return transactions


def extract_money_values(text):

    matches = re.findall(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?", text)

    values = []

    for m in matches:
        try:
            val = float(m.replace(",", ""))
            if 0 < val < 50000000:
                values.append(val)
        except:
            continue

    return values
