"""Lookup helpers for WPS and NDE search interactions."""

from __future__ import annotations

from typing import Any, Dict, List


def build_wps_query(as_string: str = "", as_dict: Dict[str, Any] | None = None) -> Dict[str, Any] | str:
    as_dict = as_dict or {}

    line_class: str = ""
    dia_in: List = []

    try:
        if as_string and as_string.strip():
            return as_string
    except Exception:
        pass

    if not line_class:
        try:
            line_class = (as_dict.get("line_class") or "").strip()
        except Exception:
            pass

    try:
        raw = as_dict.get("dia_in")
        if isinstance(raw, list):
            dia_in = raw
    except Exception:
        pass

    filters = []
    if len(dia_in):
        value = dia_in[-1]
        filters.append(f"dia_in1 le {value} and dia_in2 ge {value}")

    return {
        "search": line_class if line_class else "*",
        "queryType": "semantic",
        "semanticConfiguration": "wps-diain-semantic-configuration",
        "filter": " and ".join(filters) if filters else "",
        "top": 6,
    }


def check_nde_search(input1: list, line_class: str) -> str:
    if not input1:
        return None

    if line_class not in input1[0].get("text", ""):
        return None

    if input1 and input1[0].get("metadata") == 100:
        return "Yes"
    return "No"