"""Lookup test for the Azure AI Search indexes used by the job-pack flow.

This test exercises a known line-class family that appears in the migration
notes and verifies that both WPS/PWHT and NDE indexes return a matching result.
It runs through the current Azure CLI login and is intended to be executed with
the maf virtual environment.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


DEFAULT_ENDPOINT = "https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net"
DEFAULT_API_VERSION = "2023-11-01"
DEFAULT_LINE_CLASS = "150H25"
DEFAULT_WPS_INDEX = "wps-diain"
DEFAULT_NDE_INDEX = "ndeee"


def resolve_az_command() -> str:
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
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
        path = Path(candidate)
        if path.is_file():
            return str(path)

    raise FileNotFoundError("Could not locate Azure CLI. Ensure az is installed and available.")


def get_access_token() -> str:
    command = [
        resolve_az_command(),
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


def search_index(endpoint: str, api_version: str, token: str, index_name: str, query: str) -> list[dict]:
    body = json.dumps(
        {
            "search": query,
            "top": 5,
        }
    )
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
    env["AZURE_SEARCH_URI"] = f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
    env["AZURE_SEARCH_BODY"] = body

    completed = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
    payload = json.loads(completed.stdout)
    return payload.get("value", [])


def find_matching_document(documents: list[dict], expected_line_class: str) -> dict | None:
    normalized_expected = expected_line_class.upper().replace(" ", "")
    for document in documents:
        line_class = str(document.get("line_class", "")).upper().replace(" ", "")
        if normalized_expected in line_class:
            return document
    return None


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check line-class lookup behavior in Azure AI Search")
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
        "--line-class",
        default=os.environ.get("AZURE_SEARCH_LINE_CLASS", DEFAULT_LINE_CLASS),
        help="Expected line-class family to search for",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    try:
        token = get_access_token()
    except (subprocess.CalledProcessError, OSError, RuntimeError) as exc:
        print(f"Failed to get Azure CLI access token: {exc}", file=sys.stderr)
        return 1

    try:
        wps_docs = search_index(args.endpoint, args.api_version, token, DEFAULT_WPS_INDEX, args.line_class)
        nde_docs = search_index(args.endpoint, args.api_version, token, DEFAULT_NDE_INDEX, args.line_class)
    except subprocess.CalledProcessError as exc:
        print("Search request failed while invoking PowerShell", file=sys.stderr)
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        return 2

    wps_match = find_matching_document(wps_docs, args.line_class)
    nde_match = find_matching_document(nde_docs, args.line_class)

    if wps_match is None:
        print(f"No WPS match found for line class family {args.line_class}", file=sys.stderr)
        return 3
    if nde_match is None:
        print(f"No NDE match found for line class family {args.line_class}", file=sys.stderr)
        return 4

    print(f"WPS match: {wps_match.get('line_class')}")
    print(f"WPS pwht: {wps_match.get('pwht')}")
    print(f"WPS fields: {', '.join(sorted(wps_match.keys()))}")
    print(f"NDE match: {nde_match.get('line_class')}")
    print(f"NDE pmi_percent: {nde_match.get('pmi_percent')}")
    print(f"NDE fields: {', '.join(sorted(nde_match.keys()))}")
    print("Azure AI Search line-class lookup test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))