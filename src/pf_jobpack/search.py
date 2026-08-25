"""Azure AI Search helpers."""

from __future__ import annotations

import requests


def _clean(value: str) -> str:
    return value.strip().strip('"').strip("'").rstrip("/")


def acs_search(endpoint: str, index_name: str, api_key: str, api_version: str, body: dict) -> dict:
    endpoint = _clean(endpoint)
    index_name = _clean(index_name)
    api_version = _clean(api_version)

    url = f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
    headers = {"Content-Type": "application/json", "api-key": api_key}

    response = requests.post(url, headers=headers, json=body, timeout=60)
    response.raise_for_status()
    return response.json()