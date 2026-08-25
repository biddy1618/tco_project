"""Azure AI Search query building + HTTP client.

Faithful port of the original ``wps_json_builder.py`` (query building) and
``wps_api.py`` (search call) nodes.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Union

import requests


# --------------------------------------------------------------------------- #
# WPS query building (wps_json_builder)
# --------------------------------------------------------------------------- #
def build_wps_query(as_string: str = "", as_dict: Dict[str, Any] | None = None) -> Union[str, Dict[str, Any]]:
    """Build the Azure AI Search body for the WPS lookup.

    If the router produced a plain string (a follow-up question rather than a
    finalized state), that string is passed straight through untouched.
    """
    as_dict = as_dict or {}

    line_class: str = ""
    dia_in: List = []

    # Step 1: prioritize as_string (a pending question) — pass it through.
    try:
        if as_string and as_string.strip():
            return as_string
    except Exception:
        pass

    # Step 2: otherwise pull the search terms from the state dict.
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
        value = dia_in[-1]  # last actual element
        filters.append(f"dia_in1 le {value} and dia_in2 ge {value}")

    return {
        "search": line_class if line_class else "*",
        "queryType": "semantic",
        "semanticConfiguration": "wps-diain-semantic-configuration",
        "filter": " and ".join(filters) if filters else "",
        "top": 6,
    }


# --------------------------------------------------------------------------- #
# Azure AI Search call (wps_api)
# --------------------------------------------------------------------------- #
def _clean(s: str) -> str:
    """Strip whitespace, wrapping quotes, and trailing slashes."""
    return s.strip().strip('"').strip("'").rstrip("/")


def acs_search(
    endpoint: str,
    index_name: str,
    api_key: str,
    api_version: str,
    body: Any,
) -> Union[str, Dict[str, Any]]:
    """Run an Azure AI Search query, tolerating string pass-through payloads."""
    # Case 1: upstream sent a plain string.
    if isinstance(body, str):
        try:
            maybe = json.loads(body)
            if isinstance(maybe, dict):
                body = maybe  # fall through to the search branch
        except Exception:
            return body.strip()  # truly a string -> return as-is

    # Case 2: not a dict and not parseable JSON -> return safely.
    if not isinstance(body, dict):
        return str(body) if body is not None else ""

    # Case 3: dict/JSON -> run the search.
    endpoint = _clean(endpoint)
    index_name = _clean(index_name)
    api_version = _clean(api_version)

    url = f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
    headers = {"Content-Type": "application/json", "api-key": api_key}

    try:
        r = requests.post(url, headers=headers, json=body, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        # graceful failure so the flow doesn't crash
        return {"error": "search_failed", "detail": str(e), "value": []}
