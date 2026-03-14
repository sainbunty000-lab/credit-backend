from pathlib import Path
import re

p = Path("services/ocr_image_extractor.py")
s = p.read_text(encoding="utf-8")

# Replace the whole function definition
s = re.sub(
    r"def extract_amount_from_line\(line: str\):[\s\S]*?$",
    """def extract_amount_from_line(line: str):
    \"""
    Extract the most plausible amount from a line.
    Handles common OCR issues:
      - Indian commas: 13,93,827
      - spaces inside number: 13 93 827
      - dots used as separators: 13.93.827
      - parentheses negatives: (123)
    Returns the largest-magnitude parsed value.
    \"""
    s = str(line)

    # negatives in parentheses
    s = re.sub(r"\\(([^)]+)\\)", r"-\\1", s)

    # normalize separators inside numbers
    # 13 93 827 -> 13,93,827 (join spaces between digit groups)
    s = re.sub(r"(?<=\\d)\\s+(?=\\d)", "", s)

    # 13.93.827 -> 13,93,827 (dots as group separators)
    s = re.sub(r"(?<=\\d)\\.(?=\\d{2,3}(\\D|$))", ",", s)

    # capture number candidates (allows Indian grouping)
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
""",
    s,
    flags=re.M
)

p.write_text(s, encoding="utf-8")
print("Updated services/ocr_image_extractor.py")
