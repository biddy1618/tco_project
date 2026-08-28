"""Resolve Tracker test IDs to the deducted prompt Prompt Flow actually ran.

The MAF slices take free-text ``question`` the same way Prompt Flow did. Nur's
Tracker IDs (``TC-001`` …) are labels, not the repair-scope text. If you pass
``TC-002`` as the question, extraction sees those six characters — it does not
open the spreadsheet. This helper maps a bare ``TC-NNN`` to sheet
``2. Test Cases`` column ``Deducted prompt`` (frozen in ``tracker_cases.json``).
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_CASES_PATH = Path(__file__).with_name("tracker_cases.json")
_TC_ID = re.compile(r"^TC-\d{3}$", re.IGNORECASE)


@lru_cache(maxsize=1)
def load_cases() -> dict[str, dict]:
    if not _CASES_PATH.is_file():
        raise FileNotFoundError(
            f"Tracker case file missing: {_CASES_PATH}. "
            "Re-export sheet '2. Test Cases' from the baseline workbook."
        )
    raw = json.loads(_CASES_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"No test cases in {_CASES_PATH}")
    return raw


def deducted_prompt(test_id: str) -> str:
    """Return the Tracker deducted prompt for ``TC-001``-style IDs."""
    cases = load_cases()
    key = test_id.strip().upper()
    row = cases.get(key)
    if row is None:
        known = ", ".join(sorted(cases))
        raise KeyError(f"Unknown test ID {key!r}. Known: {known}")
    prompt = (row.get("deducted_prompt") or "").strip()
    if not prompt:
        raise ValueError(f"{key} has an empty deducted prompt")
    return prompt


def resolve_question(raw: str) -> str:
    """If ``raw`` is a Tracker test ID, return its deducted prompt; else unchanged."""
    text = (raw or "").strip()
    if _TC_ID.fullmatch(text):
        return deducted_prompt(text)
    return text


TC001 = deducted_prompt("TC-001")
