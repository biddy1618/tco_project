"""Post-weld heat-treatment (PWHT) flag evaluation.

Faithful port of the original ``pwht_check.py`` node.
"""

from __future__ import annotations

from typing import Any, Union

_DIA_MISMATCH_MSG = (
    "Please recheck your diameter — the mismatch might come from the diameter range value. "
    "Your diameter could be listed in the WPS table."
)


def check_pwht_flag(search_result: Any, line_class: str) -> Union[str, None]:
    # Case 1: upstream passed a plain string -> return it as-is.
    if isinstance(search_result, str):
        return search_result.strip() if search_result else None

    # Case 2: no line_class provided -> skip evaluation.
    if not line_class:
        return None

    # Case 3: validate structure.
    if not isinstance(search_result, dict):
        return _DIA_MISMATCH_MSG
    if "value" not in search_result or not search_result["value"]:
        return _DIA_MISMATCH_MSG

    row = search_result["value"][0] or {}
    result_line_class = (row.get("line_class") or "").upper().strip()
    input_line_class = line_class.upper().strip()

    # Case 4: line_class mismatch.
    if not result_line_class:
        return f"I couldn't find a matching line class for '{line_class}' in the WPS table. "
    if input_line_class not in result_line_class:
        return _DIA_MISMATCH_MSG

    # Case 5: matched -> evaluate PWHT.
    pwht = row.get("pwht")
    if not pwht or not isinstance(pwht, str):
        return None

    pwht_clean = pwht.strip().upper()
    if not pwht_clean:
        return None

    return "Yes" if pwht_clean.startswith("Y") else "No"
