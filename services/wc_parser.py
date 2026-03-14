cd ~/credit-backend/credit-backend

cat > services/wc_parser.py <<'PY'
import re
from io import BytesIO
from difflib import SequenceMatcher

import pandas as pd
import pdfplumber

from services.accounting_dictionary import ACCOUNTING_KEYWORDS, UNIT_SCALE_KEYWORDS


# ==========================================================
# A) Unit detection (“In Thousands/Lakhs/Crores”) + multiply
# ==========================================================

def _contains_any(text: str, keywords: list[str]) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)


def detect_multiplier(text: str) -> int:
    """
    Detect unit scale from document text.
    Supports 'thousand' variants even if UNIT_SCALE_KEYWORDS is incomplete.
    """
    text = (text or "").lower()

    thousand_variants = [
        "in thousand", "in thousands",
        "(in thousand)", "(in thousands)",
        "rs. in thousand", "rs. in thousands",
        "rs in thousand", "rs in thousands",
        "₹ in thousand", "₹ in thousands",
        "in '000", "in 000", "('000)", "(000)",
        "in thousands of rupees",
    ]
    if _contains_any(text, thousand_variants):
        return 1000

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


def resolve_multiplier(detected_multiplier: int) -> int:
    return detected_multiplier if detected_multiplier and detected_multiplier != 1 else 1


# ==========================================================
# Helpers
# ==========================================================

def fuzzy_match(keyword: str, text: str, threshold: float = 0.82) -> bool:
    return SequenceMatcher(None, keyword, text).ratio() >= threshold


def _extract_number(s: str):
    s = str(s)
    s = re.sub(r"\(([^)]+)\)", r"-\1", s)  # (123) => -123
    matches = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", s)
    if not matches:
        return None
    m = matches[-1].replace(",", "")
    try:
        val = float(m)
        # avoid treating year as value
        if 1900 <= val <= 2100:
            return None
        return val
    except Exception:
        return None


def extract_numbers(values):
    out = []
    for v in values:
        n = _extract_number(v)
        if n is not None:
            out.append(n)
    return out


def pick_latest_value(numbers):
    filtered = [n for n in numbers if not (1900 <= n <= 2100)]
    return (filtered or numbers)[-1]


# ==========================================================
# B) Proper table extraction = pick value under latest year column
# ==========================================================

def _is_year_token(s: str) -> bool:
    try:
        n = int(float(str(s).strip().replace(",", "")))
        return 1900 <= n <= 2100
    except Exception:
        return False


def _find_year_header_row_and_cols(df: pd.DataFrame):
    """
    Find a row that contains year tokens and pick the max year column as "latest".
    Returns: (header_row_index, year_col_indices, latest_year_col_index)
    """
    best_header_row = None
    best_year_cols = []
    best_latest_year_col = None

    for r in range(min(len(df.index), 30)):
        row = df.iloc[r].tolist()
        year_cols = []
        years = []
        for c, cell in enumerate(row):
            if _is_year_token(str(cell).strip()):
                year_cols.append(c)
                years.append(int(float(str(cell).strip().replace(",", ""))))
        if year_cols:
            max_year = max(years)
            max_year_col = year_cols[years.index(max_year)]
            if best_header_row is None or len(year_cols) > len(best_year_cols):
                best_header_row = r
                best_year_cols = year_cols
                best_latest_year_col = max_year_col

    return best_header_row, best_year_cols, best_latest_year_col


def _pick_value_from_row_by_year_col(row_values, latest_year_col_idx):
    if latest_year_col_idx is None:
        return None
    if latest_year_col_idx < 0 or latest_year_col_idx >= len(row_values):
        return None
    return _extract_number(row_values[latest_year_col_idx])


def parse_financial_table(df: pd.DataFrame, multiplier: int) -> dict:
    result = {}

    header_row_idx, _year_cols, latest_year_col = _find_year_header_row_and_cols(df)

    for r_idx, row in df.iterrows():
        row_values = [str(v) for v in row.tolist()]

        if header_row_idx is not None and r_idx == header_row_idx:
            continue

        row_text = " ".join([v for v in row_values if v and v.strip()]).lower()
        if not row_text.strip():
            continue

        value = _pick_value_from_row_by_year_col(row_values, latest_year_col)

        # fallback: right-most number in row (common when header row not detected)
        if value is None:
            numbers = extract_numbers(row_values)
            if not numbers:
                continue
            value = pick_latest_value(numbers)

        value = value * multiplier

        # don't drop small values
        if abs(value) < 1:
            continue

        for key, keywords in ACCOUNTING_KEYWORDS.items():
            if key in result:
                continue
            for kw in keywords:
                if kw in row_text or fuzzy_match(kw, row_text):
                    result[key] = value
                    break

    return result


# ==========================================================
# C) Mapping + computed totals
# ==========================================================

def _sum_present(inputs: dict, keys: list[str]) -> float:
    total = 0.0
    found = False
    for k in keys:
        v = inputs.get(k)
        if v is None:
            continue
        try:
            total += float(v)
            found = True
        except Exception:
            continue
    return total if found else 0.0


def normalize_wc_inputs(inputs: dict) -> dict:
    """
    If current_assets/current_liabilities are not explicitly present,
    compute them from available components.
    """
    inputs = dict(inputs or {})

    if not inputs.get("current_assets"):
        ca = _sum_present(inputs, [
            "inventory",
            "receivables",
            "cash_bank",
            "short_term_loans_and_advances",
            "other_current_assets",
        ])
        if ca:
            inputs["current_assets"] = ca

    if not inputs.get("current_liabilities"):
        cl = _sum_present(inputs, [
            "payables",
            "bank_credit",
            "short_term_provisions",
            "other_current_liabilities",
        ])
        if cl:
            inputs["current_liabilities"] = cl

    return inputs


# ==========================================================
# Format parsers
# ==========================================================

def parse_pdf_tables(file_bytes: bytes) -> dict:
    result = {}
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            mult_used = resolve_multiplier(detect_multiplier(text))

            tables = page.extract_tables() or []
            for table in tables:
                df = pd.DataFrame(table).fillna("")
                table_result = parse_financial_table(df, mult_used)
                for k, v in table_result.items():
                    if k not in result:
                        result[k] = v
    return result


def parse_pdf_text(file_bytes: bytes) -> dict:
    """
    Fallback when no tables extracted: scan lines.
    """
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        all_text = "\n".join([(p.extract_text() or "") for p in pdf.pages])
    mult_used = resolve_multiplier(detect_multiplier(all_text))

    result = {}
    for line in all_text.splitlines():
        row_text = line.lower()
        n = _extract_number(line)
        if n is None:
            continue
        value = n * mult_used
        if abs(value) < 1:
            continue

        for key, keywords in ACCOUNTING_KEYWORDS.items():
            if key in result:
                continue
            for kw in keywords:
                if kw in row_text or fuzzy_match(kw, row_text):
                    result[key] = value
                    break
    return result


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
# Entry point
# ==========================================================

def parse_financial_file(file, filename):
    if isinstance(file, bytes):
        file_bytes = file
    else:
        file_bytes = file.read()

    filename_lower = (filename or "").lower()

    if filename_lower.endswith(".pdf"):
        extracted = parse_pdf_tables(file_bytes)
        if not extracted:
            extracted = parse_pdf_text(file_bytes)

    elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        extracted = parse_excel(file_bytes)

    elif filename_lower.endswith(".csv"):
        extracted = parse_csv(file_bytes)

    # NOTE: images not supported in this repo yet (no OCR module present)
    elif filename_lower.endswith(".jpg") or filename_lower.endswith(".jpeg") or filename_lower.endswith(".png"):
        extracted = {}

    else:
        extracted = {}

    extracted = normalize_wc_inputs(extracted)
    calculations = calculate_financial_metrics(extracted)
    return {"inputs": extracted, "calculations": calculations}


# ==========================================================
# Calculations (unchanged)
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
        "net_margin": net_margin,
    }
PY
