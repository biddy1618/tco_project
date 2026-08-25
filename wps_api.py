from promptflow import tool
from typing import Any, Union, Dict
import requests
import json


def _clean(s: str) -> str:
    # remove whitespace + wrapping quotes + trailing slashes
    return s.strip().strip('"').strip("'").rstrip("/")


@tool
def acs_search(
    endpoint: str,
    index_name: str,
    api_key: str,
    api_version: str,
    body: Any,
) -> Union[str, Dict[str, Any]]:

    # --- Case 1: previous node sent a plain string → just pass it through ---
    if isinstance(body, str):
        # If upstream accidentally sent a JSON-encoded dict as string, upgrade it
        try:
            maybe = json.loads(body)
            if isinstance(maybe, dict):
                body = maybe   # fall through to search branch
        except Exception:
            return body.strip()   # truly a string → return as-is

    # --- Case 2: not a dict (and not a parseable JSON string) → return safely ---
    if not isinstance(body, dict):
        return str(body) if body is not None else ""

    # --- Case 3: dict/JSON → run Azure AI Search ---
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