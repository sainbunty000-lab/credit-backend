from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Dict, List, Optional, Tuple

from PIL import Image
import pytesseract

YEAR_RE = re.compile(r"(19|20)\d{2}")
NUM_RE = re.compile(r"-?\d[\d,]*\.?\d*")


@dataclass
class OcrToken:
    text: str
    left: int
    top: int
    width: int
    height: int
    conf: float


def tokens_from_image(img: Image.Image) -> List[OcrToken]:
    """
    Word-level OCR with bounding boxes for column-aware table parsing.
    """
    img = img.convert("L")
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    tokens: List[OcrToken] = []
    n = len(data["text"])

    for i in range(n):
        txt = (data["text"][i] or "").strip()
        if not txt:
            continue

        try:
            conf = float(data["conf"][i])
        except Exception:
            conf = -1

        # filter noisy words
        if conf >= 0 and conf < 35:
            continue

        tokens.append(
            OcrToken(
                text=txt,
                left=int(data["left"][i]),
                top=int(data["top"][i]),
                width=int(data["width"][i]),
                height=int(data["height"][i]),
                conf=conf,
            )
        )

    return tokens


def group_tokens_into_rows(tokens: List[OcrToken], row_tol: int = 12) -> List[List[OcrToken]]:
    tokens = sorted(tokens, key=lambda t: (t.top, t.left))
    rows: List[List[OcrToken]] = []

    for tok in tokens:
        placed = False
        for row in rows:
            if abs(row[0].top - tok.top) <= row_tol:
                row.append(tok)
                placed = True
                break
        if not placed:
            rows.append([tok])

    for row in rows:
        row.sort(key=lambda t: t.left)

    return rows


def normalize_number_text(s: str) -> Optional[float]:
    """
    Handles commas and parentheses negatives.
    """
    s = (s or "").strip()
    if not s:
        return None

    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]

    s = s.replace(",", "")
    s = s.replace("₹", "").replace("Rs.", "").replace("INR", "").strip()

    m = NUM_RE.search(s)
    if not m:
        return None

    try:
        return float(m.group())
    except Exception:
        return None


def detect_multiplier_from_rows(rows: List[List[OcrToken]]) -> int:
    """
    Detect unit only if explicitly present; otherwise return 1.
    """
    header_text = " ".join(tok.text.lower() for row in rows[:35] for tok in row)
    header_text = " ".join(header_text.split())

    if "thousand" in header_text or "thousands" in header_text:
        return 1000
    if "lakh" in header_text or "lakhs" in header_text:
        return 100000
    if "crore" in header_text or "crores" in header_text:
        return 10000000
    if "million" in header_text or "millions" in header_text:
        return 1000000

    # common shorthand
    if "in '000" in header_text or "in 000" in header_text or "(000)" in header_text:
        return 1000

    return 1


def detect_year_columns(rows: List[List[OcrToken]]) -> List[Tuple[int, int]]:
    """
    Returns list of (year, x_center) sorted by x_center.
    """
    candidates: List[Tuple[int, int]] = []

    for row in rows[:40]:
        for tok in row:
            m = YEAR_RE.search(tok.text)
            if not m:
                continue
            year = int(m.group())
            x_center = tok.left + tok.width // 2
            candidates.append((year, x_center))

    by_year: Dict[int, List[int]] = {}
    for year, x in candidates:
        by_year.setdefault(year, []).append(x)

    out: List[Tuple[int, int]] = []
    for year, xs in by_year.items():
        xs.sort()
        out.append((year, xs[len(xs) // 2]))  # median x
    out.sort(key=lambda t: t[1])
    return out


def latest_year(year_cols: List[Tuple[int, int]]) -> Optional[int]:
    if not year_cols:
        return None
    return max(y for y, _x in year_cols)


def pick_value_from_row(
    row: List[OcrToken],
    year_cols: List[Tuple[int, int]],
    prefer_year: Optional[int],
) -> Optional[float]:
    """
    Pick number closest to the preferred year column.
    Fallback: right-most number in row.
    """
    nums: List[Tuple[float, int]] = []
    for tok in row:
        v = normalize_number_text(tok.text)
        if v is None:
            continue
        x_center = tok.left + tok.width // 2
        nums.append((v, x_center))

    if not nums:
        return None

    if year_cols and prefer_year:
        yr_map = {y: x for y, x in year_cols}
        target_x = yr_map.get(prefer_year, year_cols[-1][1])
        nums.sort(key=lambda p: abs(p[1] - target_x))
        return nums[0][0]

    nums.sort(key=lambda p: p[1])
    return nums[-1][0]


def extract_rows_years_multiplier_from_image_bytes(image_bytes: bytes):
    img = Image.open(BytesIO(image_bytes))
    tokens = tokens_from_image(img)
    rows = group_tokens_into_rows(tokens)
    year_cols = detect_year_columns(rows)
    mult = detect_multiplier_from_rows(rows)
    return rows, year_cols, mult
