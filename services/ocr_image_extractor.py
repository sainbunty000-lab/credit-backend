import re
from io import BytesIO

from PIL import Image, ImageOps, ImageEnhance
import pytesseract


def _preprocess(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(2.0)

    # upscale improves OCR a lot on statements
    w, h = img.size
    img = img.resize((int(w * 2), int(h * 2)))
    return img


def ocr_text_from_image_bytes(image_bytes: bytes) -> str:
    img = Image.open(BytesIO(image_bytes))
    img = _preprocess(img)

    # psm 6: assume a uniform block of text
    config = "--oem 3 --psm 6"
    return pytesseract.image_to_string(img, config=config)

_AMOUNT_RE = re.compile(r"-?\d+(?:,\d{2})*(?:,\d{3})*(?:\.\d+)?")

def extract_amounts_from_line(line: str) -> list[float]:
    """
    Extract all numeric tokens from a line in left-to-right order.
    Handles Indian comma formats and (123) negatives.
    """
    s = str(line)
    s = re.sub(r"\(([^)]+)\)", r"-\1", s)

    matches = _AMOUNT_RE.findall(s)
    out: list[float] = []
    for m in matches:
        try:
            out.append(float(m.replace(",", "")))
        except Exception:
            continue
    return out

def extract_leftmost_amount_from_line(line: str):
    """
    Return the left-most *money amount* from a line, skipping:
      - years (1900-2100)
      - note numbers (small integers 1..99) when there is at least one decimal amount on the line
    This is useful for statements with two year columns (2024, 2023) and note numbers.
    """
    s = str(line)
    s = re.sub(r"\(([^)]+)\)", r"-\1", s)

    tokens = _AMOUNT_RE.findall(s)
    if not tokens:
        return None

    # convert + drop years
    cleaned: list[tuple[str, float]] = []
    for t in tokens:
        try:
            v = float(t.replace(",", ""))
        except Exception:
            continue
        if v.is_integer() and 1900 <= int(v) <= 2100:
            continue
        cleaned.append((t, v))

    if not cleaned:
        return None

    has_decimal_amount = any("." in t for t, _ in cleaned)

    if has_decimal_amount:
        # skip note numbers like 1,2,3... that appear before real amounts
        for _t, v in cleaned:
            if v.is_integer() and 1 <= int(v) <= 99:
                continue
            return v

    # fallback: return first non-note integer/float
    for _t, v in cleaned:
        if v.is_integer() and 1 <= int(v) <= 99:
            continue
        return v

    return None

def extract_amount_from_line(line: str):
    """
    Extract the largest numeric token from a line.
    Handles Indian comma formats and (123) negatives.
    """
    vals = extract_amounts_from_line(line)
    if not vals:
        return None
    return max(vals, key=lambda x: abs(x))
