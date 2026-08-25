from promptflow import tool
import requests

def _clean(s: str) -> str:
    # remove whitespace + wrapping quotes + trailing slashes
    return s.strip().strip('"').strip("'").rstrip("/")

@tool
def acs_search(endpoint: str, index_name: str, api_key: str, api_version: str, body: dict) -> dict:
    endpoint = _clean(endpoint)
    index_name = _clean(index_name)
    api_version = _clean(api_version)

    url = f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
    headers = {"Content-Type": "application/json", "api-key": api_key}

    r = requests.post(url, headers=headers, json=body, timeout=60)
    r.raise_for_status()
    return r.json()