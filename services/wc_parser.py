import pdfplumber
import pandas as pd
import re
from io import BytesIO
from difflib import SequenceMatcher

from services.accounting_dictionary import ACCOUNTING_KEYWORDS, UNIT_SCALE_KEYWORDS


# ==========================================================
# MAIN ENTRY
# ==========================================================

def parse_financial_file(file, filename):

    if isinstance(file, bytes):
        file_bytes = file
    else:
        file_bytes = file.read()

    filename = filename.lower()

    if filename.endswith(".pdf"):
        extracted = parse_pdf_tables(file_bytes)

    else:
        extracted = {}

    calculations = calculate_financial_metrics(extracted)

    return {
        "inputs": extracted,
        "calculations": calculations
    }


# ==========================================================
# PDF TABLE PARSER
# ==========================================================

def parse_pdf_tables(file_bytes):

    result = {}
    multiplier = 1

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if text:
                multiplier = detect_multiplier(text)

            tables = page.extract_tables()

            for table in tables:

                df = pd.DataFrame(table)

                table_result = parse_financial_table(df, multiplier)

                for k, v in table_result.items():
                    if k not in result:
                        result[k] = v

    return result


# ==========================================================
# TABLE PROCESSOR
# ==========================================================

def parse_financial_table(df, multiplier):

    result = {}

    for _, row in df.iterrows():

        row_values = [str(v) for v in row if v]

        if not row_values:
            continue

        row_text = " ".join(row_values).lower()

        numbers = extract_numbers(row_values)

        if not numbers:
            continue

        value = pick_latest_value(numbers) * multiplier

        if abs(value) < 100:
            continue

        for key, keywords in ACCOUNTING_KEYWORDS.items():

            if key in result:
                continue

            for keyword in keywords:

                if keyword in row_text or fuzzy_match(keyword, row_text):

                    result[key] = value

    return result


# ==========================================================
# FUZZY MATCH
# ==========================================================

def fuzzy_match(keyword, text, threshold=0.82):

    ratio = SequenceMatcher(None, keyword, text).ratio()

    return ratio >= threshold


# ==========================================================
# NUMBER EXTRACTION
# ==========================================================

def extract_numbers(values):

    numbers = []

    for v in values:

        matches = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", str(v))

        for m in matches:

            m = m.replace(",", "")

            try:

                val = float(m)

                if 1900 <= val <= 2100:
                    continue

                numbers.append(val)
            except Exception:
                pass

    return numbers


# ==========================================================
# PICK LATEST YEAR COLUMN
# ==========================================================

def pick_latest_value(numbers):

    if len(numbers) >= 2:
        return numbers[-2]

    return numbers[-1]


# ==========================================================
# UNIT DETECTION
# ==========================================================

def detect_multiplier(text):

    text = text.lower()

    for unit, keywords in UNIT_SCALE_KEYWORDS.items():

        for k in keywords:

            if k in text:

                if unit == "thousand":
                    return 1000

                if unit == "lakh":
                    return 100000

                if unit == "million":
                    return 1000000

                if unit == "crore":
                    return 10000000

    return 1


# ==========================================================
# FINANCIAL CALCULATIONS
# ==========================================================

def calculate_financial_metrics(data):

    sales = data.get("annual_sales", 0)
    other_income = data.get("other_income", 0)
    expenses = data.get("operating_expenses", 0)

    interest = data.get("interest_expense", 0)
    depreciation = data.get("depreciation", 0)
    tax = data.get("tax", 0)

    equity = data.get("equity_share_capital", 0)
    reserves = data.get("reserves", 0)

    short_debt = data.get("short_term_debt", 0)
    long_debt = data.get("long_term_debt", 0)
    unsecured = data.get("unsecured_loans", 0)

    current_assets = data.get("current_assets", 0)
    current_liabilities = data.get("current_liabilities", 0)

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
