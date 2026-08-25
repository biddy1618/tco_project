"""NDE (non-destructive examination) lookup evaluation.

Port of the original ``nde_py.py`` node. Two defensive guards are added
relative to the original (empty-result check, and ``.get("text", "")``) so an
empty or malformed search result returns ``None`` instead of raising
``IndexError``/``TypeError``. Behavior for valid inputs is unchanged.
"""

from __future__ import annotations

from typing import List, Optional


def check_nde_search(input1: List[dict], line_class: str) -> Optional[str]:
    if not input1:
        return None

    if line_class not in (input1[0].get("text", "") or ""):
        return None

    if input1[0].get("metadata") == 100:
        return "Yes"
    return "No"
