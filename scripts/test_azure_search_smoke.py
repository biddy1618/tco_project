"""Smoke-test Azure AI Search connectivity from the local machine.

This script uses the current `az login` session to get an AAD access token for
the Azure AI Search data plane, then issues a minimal search request against the
project indexes.

It does not require any extra Python packages.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import shutil
from typing import Iterable
from pathlib import Path


DEFAULT_ENDPOINT = "https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net"
DEFAULT_API_VERSION = "2023-11-01"
DEFAULT_INDEXES = ("wps-diain", "ndeee")


def resolve_az_command() -> list[str]:
    candidates = [
        "az",
        "az.cmd",
        str(
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Programs"
            / "AzureCLI"
            / "Microsoft SDKs"
            / "Azure"
            / "CLI2"
            / "wbin"
            / "az.cmd"
        ),
    ]

    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if path.is_file():
            return [str(path)]
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved]

    raise FileNotFoundError("Could not locate the Azure CLI executable. Install Azure CLI or add it to PATH.")


def get_access_token() -> str:
    command = resolve_az_command() + [
        "account",
        "get-access-token",
        "--resource",
        "https://search.azure.com/",
        "--query",
        "accessToken",
        "-o",
        "tsv",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    token = completed.stdout.strip()
    if not token:
        raise RuntimeError("Azure CLI returned an empty access token")
    return token


def run_search(endpoint: str, api_version: str, token: str, index_name: str, search_text: str) -> list[dict]:
    url = f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
    body = json.dumps({"search": search_text, "top": 1})
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        (
            "$headers = @{ Authorization = 'Bearer ' + $env:AZURE_SEARCH_TOKEN; 'Content-Type' = 'application/json' }; "
            "$result = Invoke-RestMethod -Method Post -Uri $env:AZURE_SEARCH_URI -Headers $headers -Body $env:AZURE_SEARCH_BODY; "
            "$result | ConvertTo-Json -Depth 10"
        ),
    ]
    env = os.environ.copy()
    env["AZURE_SEARCH_TOKEN"] = token
    env["AZURE_SEARCH_URI"] = url
    env["AZURE_SEARCH_BODY"] = body

    completed = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
    payload = json.loads(completed.stdout)
    return payload.get("value", [])


def summarize_documents(index_name: str, documents: list[dict]) -> None:
    if not documents:
        print(f"{index_name}: no documents returned")
        return

    document = documents[0]
    visible_keys = [key for key in document.keys() if key != "@search.score"]
    print(f"{index_name}: ok, returned {len(documents)} document(s)")
    print(f"{index_name}: keys = {', '.join(visible_keys)}")
    if "line_class" in document:
        print(f"{index_name}: line_class = {document['line_class']}")
    if "pwht" in document:
        print(f"{index_name}: pwht = {document['pwht']}")
    if "pmi_percent" in document:
        print(f"{index_name}: pmi_percent = {document['pmi_percent']}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test Azure AI Search access")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("AZURE_SEARCH_ENDPOINT", DEFAULT_ENDPOINT),
        help="Azure AI Search endpoint",
    )
    parser.add_argument(
        "--api-version",
        default=os.environ.get("AZURE_SEARCH_API_VERSION", DEFAULT_API_VERSION),
        help="Azure AI Search REST API version",
    )
    parser.add_argument(
        "--search-text",
        default=os.environ.get("AZURE_SEARCH_SMOKE_QUERY", "*"),
        help="Search text used for the smoke test",
    )
    parser.add_argument(
        "--index",
        action="append",
        dest="indexes",
        help="Index name to query. Can be provided multiple times.",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    indexes = args.indexes or list(DEFAULT_INDEXES)

    try:
        token = get_access_token()
    except (subprocess.CalledProcessError, OSError, RuntimeError) as exc:
        print(f"Failed to get Azure CLI access token: {exc}", file=sys.stderr)
        return 1

    try:
        for index_name in indexes:
            print(f"--- {index_name} ---")
            documents = run_search(args.endpoint, args.api_version, token, index_name, args.search_text)
            summarize_documents(index_name, documents)
    except subprocess.CalledProcessError as exc:
        print("Search request failed while invoking PowerShell", file=sys.stderr)
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive smoke-test guard
        print(f"Unexpected failure: {exc}", file=sys.stderr)
        return 4

    print("Azure AI Search smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))