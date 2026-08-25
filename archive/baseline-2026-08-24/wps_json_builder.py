from promptflow import tool
from typing import Dict, Any, List
import requests


@tool
def my_python_tool(as_string: str = "", as_dict: Dict[str, Any] = None) -> Dict[str, Any]:
    as_dict = as_dict or {}

    line_class: str = ""
    dia_in: List = []

    # --- Step 1: prioritize as_string ---
    try:
        if as_string and as_string.strip():
            return as_string
    except Exception:
        pass

    # --- Step 2: fallback to as_dict only if as_string was empty ---
    if not line_class:
        try:
            line_class = (as_dict.get("line_class") or "").strip()
        except Exception:
            pass

    # dia_in only comes from as_dict (string branch has no thickness info)
    try:
        raw = as_dict.get("dia_in")
        if isinstance(raw, list):
            dia_in = raw
    except Exception:
        pass

    # --- build thickness filter ---
    filters = []
    if len(dia_in):
        value = dia_in[-1]  # last actual element
        filters.append(f"dia_in1 le {value} and dia_in2 ge {value}")

    return {
        "search": line_class if line_class else "*",
        "queryType": "semantic",
        "semanticConfiguration": "wps-diain-semantic-configuration",
        "filter": " and ".join(filters) if filters else "",
        "top": 6,
    }