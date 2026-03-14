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
    Extract the left-most *amount* from a line, ignoring:
      - likely note numbers (small integers like 1..100)
      - years (1900..2100)
    Useful for statements with two year columns where we want the latest (left) column.
    """
    vals = extract_amounts_from_line(line)
    if not vals:
        return None

    filtered: list[float] = []
    for v in vals:
        if float(v).is_integer():
            iv = int(v)
            if iv <= 100:          # note number
                continue
            if 1900 <= iv <= 2100: # year token
                continue
        filtered.append(v)

    if not filtered:
        return None
    return filtered[0]


def extract_amount_from_line(line: str):
    """
    Extract the largest numeric token from a line.
    Handles Indian comma formats and (123) negatives.
    """
    vals = extract_amounts_from_line(line)
    if not vals:
        return None
    return max(vals, key=lambda x: abs(x))
