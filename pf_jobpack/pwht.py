"""Post-weld heat-treatment (PWHT) flag evaluation.

Faithful port of the original ``pwht_check.py`` node, plus a line-class
match that ignores spaces so ``300H21(A)`` hits index row ``300H21 (A)``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

_DIA_MISMATCH_MSG = (
    "Please recheck your diameter — the mismatch might come from the diameter range value. "
    "Your diameter could be listed in the WPS table."
)


def _norm_line_class(value: str) -> str:
    return "".join((value or "").upper().split())


def _pick_wps_row(rows: List[Any], line_class: str) -> Optional[Dict[str, Any]]:
    """Choose the hit that matches ``line_class``, not necessarily ``value[0]``.

    Semantic search can rank a neighbor class first. Extractor spelling is
    ``300H21(A)``; live ``wps-diain`` rows use ``300H21 (A)``.
    """
    wanted = _norm_line_class(line_class)
    if not wanted:
        return None

    labeled: List[tuple[Dict[str, Any], str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        labeled.append((row, _norm_line_class(str(row.get("line_class") or ""))))

    for row, got in labeled:
        if got == wanted:
            return row
    for row, got in labeled:
        if wanted in got:
            return row
    return None


def _pwht_from_row(row: Dict[str, Any]) -> str:
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
    rows = search_result.get("value")
    if not rows:
        return _DIA_MISMATCH_MSG

    row = _pick_wps_row(rows, line_class)
    if row is None:
        first = rows[0] if isinstance(rows[0], dict) else {}
        if not (first.get("line_class") or "").strip():
            return f"I couldn't find a matching line class for '{line_class}' in the WPS table. "
        return _DIA_MISMATCH_MSG

    # Case 5: matched -> evaluate PWHT.
    return _pwht_from_row(row)
