import pdfplumber
import re
from io import BytesIO
from datetime import datetime


# =====================================================
# DATE PATTERNS
# =====================================================

DATE_PATTERNS = [
    r"\d{2}/\d{2}/\d{2}",
    r"\d{2}/\d{2}/\d{4}",
    r"\d{2}-\d{2}-\d{2}",
    r"\d{2}-\d{2}-\d{4}"
]

DATE_REGEX = re.compile("|".join(DATE_PATTERNS))


# =====================================================
# MAIN ENTRY
# =====================================================

def parse_banking_file(file_bytes):

    transactions = []

    try:

        with pdfplumber.open(BytesIO(file_bytes)) as pdf:

            for page in pdf.pages:

                # ======================================
                # TABLE PARSING
                # ======================================

                tables = page.extract_tables()

                if tables:

                    for table in tables:

                        for row in table:

                            txn = parse_table_row(row)

                            if txn:
                                transactions.append(txn)

                # ======================================
                # TEXT FALLBACK PARSING
                # ======================================

                text = page.extract_text()

                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:

                    txn = parse_text_line(line, transactions)

                    if txn:
                        transactions.append(txn)

    except Exception:
        return []

    # ======================================
    # REMOVE DUPLICATES
    # ======================================

    transactions = list({(t['date'], t['balance']): t for t in transactions}.values())

    # ======================================
    # SORT BY DATE
    # ======================================

    transactions.sort(key=lambda x: parse_date(x["date"]))

    return transactions


# =====================================================
# TABLE ROW PARSER
# =====================================================

def parse_table_row(row):

    if not row:
        return None

    try:

        date = None

        for cell in row:

            if is_date(cell):
                date = cell
                break

        if not date:
            return None

        numbers = extract_numbers(row)

        if len(numbers) < 2:
            return None

        amount = numbers[-2]
        balance = numbers[-1]

        debit = 0
        credit = 0

        row_text = " ".join([str(x).lower() for x in row])

        if "dr" in row_text:
            debit = amount

        elif "cr" in row_text:
            credit = amount

        description = extract_description(row)

        return {
            "date": date,
            "description": description,
            "debit": debit,
            "credit": credit,
            "balance": balance
        }

    except:
        return None


# =====================================================
# TEXT LINE PARSER
# =====================================================

def parse_text_line(line, transactions):

    if not line:
        return None

    date_match = DATE_REGEX.search(line)

    if not date_match:
        return None

    date = date_match.group()

    numbers = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", line)

    if len(numbers) < 2:
        return None

    balance = normalize_number(numbers[-1])
    amount = normalize_number(numbers[-2])

    debit = 0
    credit = 0

    line_lower = line.lower()

    # ======================================
    # DR / CR DETECTION
    # ======================================

    if "dr" in line_lower:
        debit = amount

    elif "cr" in line_lower:
        credit = amount

    else:

        # Balance movement fallback

        if transactions:

            prev_balance = transactions[-1]["balance"]

            if balance > prev_balance:
                credit = amount
            else:
                debit = amount

        else:

            credit = amount

    narration = clean_narration(line.replace(date, ""))

    return {
        "date": date,
        "description": narration,
        "debit": debit,
        "credit": credit,
        "balance": balance
    }


# =====================================================
# DATE HELPERS
# =====================================================

def is_date(value):

    if not value:
        return False

    value = str(value)

    return bool(DATE_REGEX.match(value))


def parse_date(date_str):

    formats = ["%d/%m/%y", "%d/%m/%Y", "%d-%m-%y", "%d-%m-%Y"]

    for f in formats:

        try:
            return datetime.strptime(date_str, f)
        except:
            continue

    return datetime.now()


# =====================================================
# NUMBER EXTRACTION
# =====================================================

def extract_numbers(values):

    numbers = []

    for v in values:

        nums = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", str(v))

        for n in nums:

            n = n.replace(",", "")

            try:
                numbers.append(float(n))
            except:
                pass

    return numbers


def normalize_number(value):

    try:

        if value is None:
            return 0

        value = str(value)

        value = value.replace(",", "")
        value = value.replace("₹", "")
        value = value.replace("Dr", "")
        value = value.replace("Cr", "")

        return float(value)

    except:
        return 0


# =====================================================
# DESCRIPTION EXTRACTION
# =====================================================

def extract_description(row):

    try:

        text = " ".join([str(x) for x in row if x])

        return clean_narration(text)

    except:
        return ""


# =====================================================
# NARRATION CLEANER
# =====================================================

def clean_narration(text):

    text = re.sub(r"\s+", " ", str(text))

    text = text.replace("\n", " ")

    return text.strip()
