cat > services/wc_missing.py <<'PY'
from __future__ import annotations

from typing import Dict, List, Tuple


def find_missing_fields_present_only(inputs: Dict, required_fields: List[str]) -> Tuple[List[str], List[str]]:
    """
    Missing = key not present OR value is None OR empty string.
    Value 0 is considered present/valid.
    """
    missing: List[str] = []
    present: List[str] = []

    for f in required_fields:
        if f not in inputs:
            missing.append(f)
            continue

        val = inputs.get(f)
        if val is None or val == "":
            missing.append(f)
        else:
            present.append(f)

    return missing, present
PY
