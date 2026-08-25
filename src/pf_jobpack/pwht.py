"""PWHT evaluation helpers for the job-pack flow."""

from __future__ import annotations

from typing import Any, Union


def check_pwht_flag(search_result: Any, line_class: str) -> Union[str, None]:
    if isinstance(search_result, str):
        return search_result.strip() if search_result else None

    if not line_class:
        return None

    if not isinstance(search_result, dict):
        return (
            f"Please recheck your diameter — the mismatch might come from the diameter range value. "
            f"Your diameter could be listed in the WPS table."
        )
    if "value" not in search_result or not search_result["value"]:
        return (
            f"Please recheck your diameter — the mismatch might come from the diameter range value. "
            f"Your diameter could be listed in the WPS table."
        )

    row = search_result["value"][0] or {}
    result_line_class = (row.get("line_class") or "").upper().strip()
    input_line_class = line_class.upper().strip()

    if not result_line_class:
        return f"I couldn't find a matching line class for '{line_class}' in the WPS table. "

    if input_line_class not in result_line_class:
        return (
            f"Please recheck your diameter — the mismatch might come from the diameter range value. "
            f"Your diameter could be listed in the WPS table."
        )

    pwht = row.get("pwht")
    if not pwht or not isinstance(pwht, str):
        return None

    pwht_clean = pwht.strip().upper()
    if not pwht_clean:
        return None

    return "Yes" if pwht_clean.startswith("Y") else "No"