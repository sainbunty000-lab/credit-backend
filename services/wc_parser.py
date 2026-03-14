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
# UNIT OVERRIDE (from dropdown)
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
    1) dropdown override
    2) detected multiplier from statement
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

def parse_financial_file(file, filename, unit_override: str | None = None, debug: bool = True):

    if isinstance(file, bytes):
        file_bytes = file
    else:
        file_bytes = file.read()

    filename_lower = (filename or "").lower()

    extracted = {}
    debug_info = {
        "filename": filename,
        "unit_override": unit_override,
        "path_used": None,
        "detected_years": [],
        "detected_multiplier": None,
        "multiplier_used": None,
        "extracted_keys_count": 0,
        "extracted_keys": [],
    }

    if filename_lower.endswith(".pdf"):
        extracted, dbg = parse_pdf_tables(file_bytes, unit_override=unit_override, debug=debug)
        if extracted:
            debug_info.update(dbg or {})
            debug_info["path_used"] = "pdf_tables"
        else:
            if not is_probably_scanned_pdf(file_bytes):
                text = extract_text_from_pdf_bytes(file_bytes)
                if text:
                    detected_mult = detect_multiplier(text)
                    mult_used = resolve_multiplier(detected_mult, unit_override)
                    extracted = parse_text_lines(text.splitlines(), mult_used)
                    debug_info["path_used"] = "pdf_text"
                    debug_info["detected_multiplier"] = detected_mult
                    debug_info["multiplier_used"] = mult_used

            if not extracted:
                extracted, dbg = parse_scanned_pdf_with_ocr(file_bytes, unit_override=unit_override, debug=debug)
                debug_info.update(dbg or {})
                debug_info["path_used"] = "pdf_ocr"

    elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        extracted = parse_excel(file_bytes)
        debug_info["path_used"] = "excel"

    elif filename_lower.endswith(".csv"):
        extracted = parse_csv(file_bytes)
        debug_info["path_used"] = "csv"

    elif filename_lower.endswith(".jpg") or filename_lower.endswith(".jpeg") or filename_lower.endswith(".png"):
        extracted, dbg = parse_image_statement(file_bytes, unit_override=unit_override, debug=debug)
        debug_info.update(dbg or {})
        debug_info["path_used"] = "image_ocr"

    else:
        extracted = {}
        debug_info["path_used"] = "unsupported"

    calculations = calculate_financial_metrics(extracted)

    debug_info["extracted_keys_count"] = len(extracted)
    debug_info["extracted_keys"] = sorted(list(extracted.keys()))

    out = {"inputs": extracted, "calculations": calculations}
    if debug:
        out["debug"] = debug_info
    return out


# ==========================================================
# OCR PARSERS
# ==========================================================

def parse_image_statement(image_bytes: bytes, unit_override: str | None = None, debug: bool = False):
    rows, year_cols, detected_mult = extract_rows_years_multiplier_from_image_bytes(image_bytes)
    prefer_year = latest_year(year_cols)

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

                    if abs(val) < 50:
                        continue

                    result[key] = val
                    break

    dbg = None
    if debug:
        dbg = {
            "detected_years": [y for y, _x in year_cols],
            "detected_multiplier": detected_mult,
            "multiplier_used": mult_used,
            "unit_override": unit_override,
            "extracted_keys_count": len(result),
            "extracted_keys": sorted(list(result.keys())),
        }

    return result, dbg


def parse_scanned_pdf_with_ocr(pdf_bytes: bytes, unit_override: str | None = None, debug: bool = False):
    merged = {}
    detected_years_union = set()
    detected_mults = []
    used_mults = []

    images = pdf_to_images(pdf_bytes, dpi=250)

    for img in images:
        buf = BytesIO()
        img.save(buf, format="PNG")
        page_bytes = buf.getvalue()

        page_res, page_dbg = parse_image_statement(page_bytes, unit_override=unit_override, debug=debug)

        for k, v in page_res.items():
            if k not in merged:
                merged[k] = v

        if debug and page_dbg:
            for y in page_dbg.get("detected_years", []):
                detected_years_union.add(y)
            detected_mults.append(page_dbg.get("detected_multiplier"))
            used_mults.append(page_dbg.get("multiplier_used"))

    dbg = None
    if debug:
        detected_mult = next((m for m in detected_mults if m is not None), None)
        mult_used = next((m for m in used_mults if m is not None), None)

        dbg = {
            "detected_years": sorted(list(detected_years_union)),
            "detected_multiplier": detected_mult,
            "multiplier_used": mult_used,
            "unit_override": unit_override,
            "extracted_keys_count": len(merged),
            "extracted_keys": sorted(list(merged.keys())),
        }

    return merged, dbg


# ==========================================================
# PDF TABLE PARSER
# ==========================================================

def parse_pdf_tables(file_bytes, unit_override: str | None = None, debug: bool = False):
    result = {}
    detected_mult_any = None
    mult_used_any = None

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            detected_mult = detect_multiplier(text)
            mult_used = resolve_multiplier(detected_mult, unit_override)

            if detected_mult_any is None:
                detected_mult_any = detected_mult
            if mult_used_any is None:
                mult_used_any = mult_used

            tables = page.extract_tables()
            for table in tables:
                df = pd.DataFrame(table)
                table_result = parse_financial_table(df, mult_used)
                for k, v in table_result.items():
                    if k not in result:
                        result[k] = v

    dbg = None
    if debug:
        dbg = {
            "detected_years": [],
            "detected_multiplier": detected_mult_any,
            "multiplier_used": mult_used_any,
            "unit_override": unit_override,
            "extracted_keys_count": len(result),
            "extracted_keys": sorted(list(result.keys())),
        }

    return result, dbg


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
        if abs(value) < 100:
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
    if len(numbers) >= 2:
        return numbers[-2]
    return numbers[-1]


# ==========================================================
# UNIT DETECTION (text PDFs)
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
