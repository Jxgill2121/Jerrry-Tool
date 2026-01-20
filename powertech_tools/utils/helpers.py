# General utility functions for Powertech Tools

import re
from typing import List


def natural_sort_key(text: str):
    """Natural sorting key that handles numbers in strings"""
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", text)]


def safe_float(s: str):
    """Safely convert string to float, return None if empty, 'INVALID' if failed"""
    s = (s or "").strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return "INVALID"


def safe_int(s: str):
    """Safely convert string to int, return None if empty, 'INVALID' if failed"""
    s = (s or "").strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except ValueError:
        return "INVALID"


def make_unique_names(names: List[str]) -> List[str]:
    """Make duplicate column names unique by appending _1, _2, etc."""
    seen = {}
    out = []
    for nm in names:
        if nm not in seen:
            seen[nm] = 0
            out.append(nm)
        else:
            seen[nm] += 1
            out.append(f"{nm}_{seen[nm]}")
    return out
