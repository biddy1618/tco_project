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
    #
    # Live data (wps-diain, 266 docs) has: N (128), Y (103), blank (18),
    # "N see Note (7)" (17). A blank value means the WPS table doesn't call for
    # PWHT, so we default it to "No" rather than None. Returning None here would
    # silence BOTH the PWHT branches and the wps_result == 'No' field-weld NDE
    # branch (line 57a) in the template, dropping NDE from the job pack for
    # those line classes. "N see Note (7)" starts with N -> "No" (safe).
    pwht = row.get("pwht")
    if not isinstance(pwht, str):
        return "No"

    pwht_clean = pwht.strip().upper()
    if not pwht_clean:
        return "No"

    return "Yes" if pwht_clean.startswith("Y") else "No"
