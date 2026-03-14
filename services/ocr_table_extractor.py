import re
from io import BytesIO

from PIL import Image, ImageOps, ImageEnhance
import pytesseract


def _preprocess(img: Image.Image) -> Image.Image:
    # convert to grayscale + increase contrast
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(2.0)
    # enlarge for better OCR
    w, h = img.size
    img = img.resize((int(w * 2), int(h * 2)))
    return img


def ocr_text_from_image_bytes(image_bytes: bytes) -> str:
    img = Image.open(BytesIO(image_bytes))
    img = _preprocess(img)

    # PSM 6 = assume a block of text; works ok for statements
    config = "--oem 3 --psm 6"
    return pytesseract.image_to_string(img, config=config)


def extract_amount_from_line(line: str):
    """
    Extract the largest numeric token from a line.
    Supports Indian comma format and (123) negatives.
    """
    s = str(line)
    s = re.sub(r"\(([^)]+)\)", r"-\1", s)
    matches = re.findall(r"-?\d+(?:,\d{2})*(?:,\d{3})*(?:\.\d+)?", s)
    if not matches:
        return None

    vals = []
    for m in matches:
        m2 = m.replace(",", "")
        try:
            vals.append(float(m2))
        except Exception:
            pass

    if not vals:
        return None

    return max(vals, key=lambda x: abs(x))
