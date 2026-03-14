from __future__ import annotations

from io import BytesIO
from typing import List

import pdfplumber
from PIL import Image

try:
    from pdf2image import convert_from_bytes
except Exception:
    convert_from_bytes = None


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract selectable text from PDF (non-scanned).
    """
    texts: List[str] = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                texts.append(t)
    return "\n".join(texts).strip()


def is_probably_scanned_pdf(pdf_bytes: bytes, min_chars: int = 50) -> bool:
    """
    Heuristic: if the PDF has very little selectable text, treat it as scanned.
    """
    return len(extract_text_from_pdf_bytes(pdf_bytes) or "") < min_chars


def pdf_to_images(pdf_bytes: bytes, dpi: int = 250) -> List[Image.Image]:
    """
    Convert PDF bytes to a list of PIL Images (one per page).
    Requires: pdf2image + poppler installed on OS.
    """
    if convert_from_bytes is None:
        raise RuntimeError("pdf2image not available (install pdf2image + poppler-utils).")
    return convert_from_bytes(pdf_bytes, dpi=dpi)
