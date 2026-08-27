"""Azure AI Search for MAF slices (WPS + ndeee).

Does not use the Prompt Flow ``api_key`` in ``flow.dag.yaml``. Prefer
``AzureCliCredential`` (already proven). ``AZURE_SEARCH_API_KEY`` is an
opt-in fallback for the live pytest path.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from pf_jobpack.search import acs_search
from maf.trace import step, warn

SEARCH_ENDPOINT = os.environ.get(
    "AZURE_SEARCH_ENDPOINT",
    "https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net",
).rstrip("/")
SEARCH_API_VERSION = os.environ.get("AZURE_SEARCH_API_VERSION", "2023-11-01")
WPS_INDEX = "wps-diain"
NDE_INDEX = "ndeee"
_SEARCH_SCOPE = "https://search.azure.com/.default"


def _bearer_token() -> str:
    from azure.identity import AzureCliCredential

    return AzureCliCredential().get_token(_SEARCH_SCOPE).token


def run_search(index_name: str, body: Any) -> Any:
    """POST /indexes/{index}/docs/search. Strings pass through (PF ``wps_api``)."""
    key = os.environ.get("AZURE_SEARCH_API_KEY")
    if key:
        step("search", index=index_name, auth="api_key")
        return acs_search(
            SEARCH_ENDPOINT, index_name, key, SEARCH_API_VERSION, body
        )

    if isinstance(body, str):
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                body = parsed
            else:
                step("search", index=index_name, passthrough=True)
                return body.strip()
        except json.JSONDecodeError:
            step("search", index=index_name, passthrough=True)
            return body.strip()
    if not isinstance(body, dict):
        step("search", index=index_name, passthrough=True)
        return str(body) if body is not None else ""

    step("search", index=index_name, auth="aad")

    url = (
        f"{SEARCH_ENDPOINT}/indexes/{index_name}/docs/search"
        f"?api-version={SEARCH_API_VERSION}"
    )
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_bearer_token()}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        warn("search", index=index_name, error=str(exc))
        return {"error": "search_failed", "detail": str(exc), "value": []}


def nde_lookup_items(line_class: str) -> list[dict]:
    """Keyword lookup on ``ndeee`` (PF ``nde`` node: Keyword, top_k=1)."""
    if not (line_class or "").strip():
        return []
    result = run_search(
        NDE_INDEX,
        {
            "search": line_class.strip(),
            "queryType": "simple",
            "searchFields": "line_class",
            "select": "line_class,content,pmi_percent",
            "top": 1,
        },
    )
    if isinstance(result, str) or not isinstance(result, dict):
        return []
    docs = result.get("value") or []
    items: list[dict] = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        items.append(
            {
                "text": doc.get("content") or "",
                "content": doc.get("content") or "",
                "metadata": doc.get("pmi_percent"),
            }
        )
    return items
