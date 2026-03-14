import pdfplumber
import pandas as pd
import re
from io import BytesIO
from difflib import SequenceMatcher

from services.accounting_dictionary import ACCOUNTING_KEYWORDS, UNIT_SCALE_KEYWORDS
from services.document_extractor import extract_text_from_pdf_bytes, is_probably_scanned_pdf, pdf_to_images
from services.ocr_table_extractor import (
    extract_rows_years_multiplier_from_image_bytes,
    latest_year,
    pick_value_from_row,
)

# ==========================================================
# UNIT OVERRIDE (internal only; router passes None => Auto)
# ==========================================================

def unit_override_multiplier(unit_override: str | None) -> int | None:
    """
    Returns:
      - int multiplier when override provided
      - None when Auto (not provided / empty / 'auto')
    """
    if unit_override is None:
        return None

    u = unit_override.strip().lower()
    if u == "" or u == "auto":
        return None

    mapping = {
        "none": 1,
        "rupees": 1,
        "inr": 1,
        "1": 1,
        "thousand": 1000,
        "k": 1000,
        "lakh": 100000,
        "lakhs": 100000,
        "million": 1000000,
        "crore": 10000000,
        "crores": 10000000,
    }

    if u not in mapping:
        raise ValueError("Invalid unit_override. Use: auto, none, thousand, lakh, crore, million.")

    return mapping[u]


def resolve_multiplier(detected_multiplier: int, unit_override: str | None) -> int:
    """
    Priority:
    1) override (if provided)
    2) detected multiplier from statement text
    3) safe default => 1
    """
    override_mult = unit_override_multiplier(unit_override)
    if override_mult is not None:
        return override_mult

    if detected_multiplier and detected_multiplier != 1:
        return detected_multiplier

    return 1


# ==========================================================
# MAIN ENTRY
# ==========================================================

def parse_financial_file(file, filename, unit_override: str | None = None, debug: bool = False):
    if isinstance(file, bytes):
        file_bytes = file
    else:
        file_bytes = file.read()

    filename_lower = (filename or "").lower()

    extracted = {}

    if filename_lower.endswith(".pdf"):
        extracted, _dbg = parse_pdf_tables(file_bytes, unit_override=unit_override, debug=False)
        if not extracted:
            if not is_probably_scanned_pdf(file_bytes):
                text = extract_text_from_pdf_bytes(file_bytes)
                if text:
                    detected_mult = detect_multiplier(text)
                    mult_used = resolve_multiplier(detected_mult, unit_override)
                    extracted = parse_text_lines(text.splitlines(), mult_used)

            if not extracted:
                extracted, _dbg = parse_scanned_pdf_with_ocr(file_bytes, unit_override=unit_override, debug=False)

    elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        extracted = parse_excel(file_bytes)

    elif filename_lower.endswith(".csv"):
        extracted = parse_csv(file_bytes)

    elif filename_lower.endswith(".jpg") or filename_lower.endswith(".jpeg") or filename_lower.endswith(".png"):
        extracted, _dbg = parse_image_statement(file_bytes, unit_override=unit_override, debug=False)

    else:
        extracted = {}

    calculations = calculate_financial_metrics(extracted)
    return {"inputs": extracted, "calculations": calculations}


# ==========================================================
# OCR PARSERS
# ==========================================================

def parse_image_statement(image_bytes: bytes, unit_override: str | None = None, debug: bool = False):
    rows, year_cols, detected_mult = extract_rows_years_multiplier_from_image_bytes(image_bytes)
    prefer_year = latest_year(year_cols)

    # Fallback: if OCR extractor didn't detect multiplier, try detecting from all OCR row text
    if not detected_mult:
        all_text = " ".join(" ".join(t.text for t in row) for row in rows)
        detected_mult = detect_multiplier(all_text)

    mult_used = resolve_multiplier(detected_mult, unit_override)

    result = {}

    for row in rows:
        row_text = " ".join(t.text for t in row).lower()

        # reduce footer noise
        if "signed in terms" in row_text or "chartered accountants" in row_text:
            continue

        for key, keywords in ACCOUNTING_KEYWORDS.items():
            if key in result:
                continue

            for kw in keywords:
                if kw in row_text or fuzzy_match(kw, row_text):
                    val = pick_value_from_row(row, year_cols, prefer_year)
                    if val is None:
                        continue

                    val = val * mult_used

                    # Don't drop small values (lakhs/crores/decimals)
                    if abs(val) < 1:
                        continue

                    result[key] = val
                    break

    return result, None


def parse_scanned_pdf_with_ocr(pdf_bytes: bytes, unit_override: str | None = None, debug: bool = False):
    merged = {}

    images = pdf_to_images(pdf_bytes, dpi=250)

    for img in images:
        buf = BytesIO()
        img.save(buf, format="PNG")
        page_bytes = buf.getvalue()

        page_res, _page_dbg = parse_image_statement(page_bytes, unit_override=unit_override, debug=False)

        for k, v in page_res.items():
            if k not in merged:
                merged[k] = v

    return merged, None


# ==========================================================
# PDF TABLE PARSER
# ==========================================================

def parse_pdf_tables(file_bytes, unit_override: str | None = None, debug: bool = False):
    result = {}

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            detected_mult = detect_multiplier(text)
            mult_used = resolve_multiplier(detected_mult, unit_override)

            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table)
                table_result = parse_financial_table(df, mult_used)
                for k, v in table_result.items():
                    if k not in result:
                        result[k] = v

    return result, None


# ==========================================================
# EXCEL/CSV
# ==========================================================

def parse_excel(file_bytes: bytes) -> dict:
    result = {}
    xls = pd.ExcelFile(BytesIO(file_bytes))
    for sheet in xls.sheet_names:
        try:
            df = xls.parse(sheet, header=None).fillna("")
            sheet_result = parse_financial_table(df, multiplier=1)
            for k, v in sheet_result.items():
                if k not in result:
                    result[k] = v
        except Exception:
            continue
    return result


def parse_csv(file_bytes: bytes) -> dict:
    try:
        df = pd.read_csv(BytesIO(file_bytes), header=None).fillna("")
    except Exception:
        df = pd.read_csv(BytesIO(file_bytes), header=None, encoding="latin-1").fillna("")
    return parse_financial_table(df, multiplier=1)


# ==========================================================
# TEXT PARSER
# ==========================================================

def parse_text_lines(lines, multiplier: int = 1) -> dict:
    result = {}
    for line in lines:
        if not line:
            continue

        row_text = str(line).lower()
        numbers = extract_numbers([line])
        if not numbers:
            continue

        value = numbers[-1] * multiplier

        # Don't drop small values (lakhs/crores/decimals)
        if abs(value) < 1:
            continue

        for key, keywords in ACCOUNTING_KEYWORDS.items():
            if key in result:
                continue

            for keyword in keywords:
                if keyword in row_text or fuzzy_match(keyword, row_text):
                    result[key] = value
                    break
    return result


# ==========================================================
# TABLE PROCESSOR (proper year-column selection)
# ==========================================================

def _is_year_token(s: str) -> bool:
    try:
        n = int(float(str(s).strip().replace(",", "")))
        return 1900 <= n <= 2100
    except Exception:
        return False


def _find_year_header_row_and_cols(df: pd.DataFrame):
    """
    Returns: (header_row_index, year_col_indices, latest_year_col_index)
    or (None, [], None) if not found.
    """
    best_header_row = None
    best_year_cols = []
    best_latest_year_col = None

    for r in range(min(len(df.index), 30)):  # scan top area for year header
        row = df.iloc[r].tolist()
        year_cols = []
        years = []
        for c, cell in enumerate(row):
            cell_str = str(cell).strip()
            if _is_year_token(cell_str):
                year_cols.append(c)
                years.append(int(float(cell_str)))

        if year_cols:
            max_year = max(years)
            max_year_col = year_cols[years.index(max_year)]
            if best_header_row is None or len(year_cols) > len(best_year_cols):
                best_header_row = r
                best_year_cols = year_cols
                best_latest_year_col = max_year_col

    return best_header_row, best_year_cols, best_latest_year_col


def _extract_number(s: str):
    s = str(s)
    s = re.sub(r"\(([^)]+)\)", r"-\1", s)  # (123) => -123
    matches = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", s)
    if not matches:
        return None
    m = matches[-1].replace(",", "")
    try:
        val = float(m)
        if 1900 <= val <= 2100:
            return None
        return val
    except Exception:
        return None


def _pick_value_from_row_by_year_col(row_values, latest_year_col_idx):
    if latest_year_col_idx is None:
        return None
    if latest_year_col_idx < 0 or latest_year_col_idx >= len(row_values):
        return None
    return _extract_number(row_values[latest_year_col_idx])


def parse_financial_table(df, multiplier):
    result = {}

    header_row_idx, _year_cols, latest_year_col = _find_year_header_row_and_cols(df)

    for r_idx, row in df.iterrows():
        row_values = [str(v) for v in row.tolist()]

        # skip header row itself
        if header_row_idx is not None and r_idx == header_row_idx:
            continue

        row_text = " ".join([v for v in row_values if v and v.strip()]).lower()
        if not row_text.strip():
            continue

        # Prefer value from latest year column
        value = _pick_value_from_row_by_year_col(row_values, latest_year_col)

        # Fallback: right-most non-year number
        if value is None:
            numbers = extract_numbers(row_values)
            if not numbers:
                continue
            value = pick_latest_value(numbers)

        value = value * multiplier

        # Don't drop small values (lakhs/crores/decimals)
        if abs(value) < 1:
            continue

        for key, keywords in ACCOUNTING_KEYWORDS.items():
            if key in result:
                continue
            for keyword in keywords:
                if keyword in row_text or fuzzy_match(keyword, row_text):
                    result[key] = value
                    break

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
        s = str(v)
        s = re.sub(r"\(([^)]+)\)", r"-\1", s)  # (123) => -123

        matches = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", s)
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


def pick_latest_value(numbers):
    # pick the right-most non-year number (usually the latest year column)
    filtered = [n for n in numbers if not (1900 <= n <= 2100)]
    if not filtered:
        return numbers[-1]
    return filtered[-1]


# ==========================================================
# UNIT DETECTION
# ==========================================================

def detect_multiplier(text):
    text = (text or "").lower()
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
