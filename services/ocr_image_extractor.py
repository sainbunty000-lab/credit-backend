python - <<'PY'
from pathlib import Path
import re

p = Path("services/ocr_image_extractor.py")
s = p.read_text(encoding="utf-8")

pat = r"def extract_amount_from_line\(line: str\):[\s\S]*?return max\(vals, key=lambda x: abs\(x\)\)\n"
m = re.search(pat, s, flags=re.M)
if not m:
    raise SystemExit("Could not find extract_amount_from_line() to patch")

replacement = """def extract_amount_from_line(line: str):
    \"""
    Extract the most plausible amount from a line.
    Handles OCR issues:
      - Indian commas: 13,93,827
      - spaces inside numbers: 13 93 827
      - dots used as separators: 13.93.827
      - parentheses negatives: (123)
    Returns the largest-magnitude parsed value.
    \"""
    s = str(line)

    # negatives in parentheses
    s = re.sub(r"\\(([^)]+)\\)", r"-\\1", s)

    # join spaces between digit groups: "13 93 827" -> "1393827"
    s = re.sub(r"(?<=\\d)\\s+(?=\\d)", "", s)

    # treat dot between digit groups as comma separator: "13.93.827" -> "13,93,827"
    s = re.sub(r"(?<=\\d)\\.(?=\\d{2,3}(\\D|$))", ",", s)

    # extract candidates (accepts Indian grouping)
    candidates = re.findall(r"-?\\d+(?:,\\d{2})*(?:,\\d{3})*(?:\\.\\d+)?", s)
    if not candidates:
        return None

    vals = []
    for c in candidates:
        try:
            vals.append(float(c.replace(",", "")))
        except Exception:
            pass

    if not vals:
        return None

    return max(vals, key=lambda x: abs(x))
"""

s2 = re.sub(pat, replacement, s, flags=re.M)
p.write_text(s2, encoding="utf-8")
print("Patched services/ocr_image_extractor.py")
PY

python -m py_compile services/ocr_image_extractor.py
sudo systemctl restart credit-backend.service
