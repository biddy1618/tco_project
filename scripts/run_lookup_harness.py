"""Local harness for the Prompt Flow lookup branch.

This script exercises the same basic path as the current flow:
- extract a line class from input text,
- normalize legacy line classes,
- build the WPS query body,
- query WPS and NDE search indexes,
- print the returned result shapes.

Run it with the `maf` virtual environment.
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

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


DEFAULT_ENDPOINT = "https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net"
DEFAULT_API_VERSION = "2023-11-01"
DEFAULT_SAMPLE_TEXT = '63-9100-SL-2153-3/4"-150H22-HCW5'
DEFAULT_WPS_INDEX = "wps-diain"
DEFAULT_NDE_INDEX = "ndeee"
from src.pf_jobpack.extraction import extract_line_class, get_legacy_class_line
from src.pf_jobpack.lookup import build_wps_query


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


def search_index(endpoint: str, api_version: str, token: str, index_name: str, body: dict[str, object]) -> list[dict]:
    url = f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
    request_body = json.dumps(body).encode("utf-8")
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
    env["AZURE_SEARCH_BODY"] = request_body.decode("utf-8")

    completed = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
    payload = json.loads(completed.stdout)
    return payload.get("value", [])


def print_document_summary(label: str, documents: list[dict]) -> None:
    print(f"{label}: returned {len(documents)} document(s)")
    if not documents:
        return
    document = documents[0]
    visible_keys = [key for key in document.keys() if key != "@search.score"]
    print(f"{label}: keys = {', '.join(visible_keys)}")
    if "line_class" in document:
        print(f"{label}: line_class = {document['line_class']}")
    if "pwht" in document:
        print(f"{label}: pwht = {document['pwht']}")
    if "pmi_percent" in document:
        print(f"{label}: pmi_percent = {document['pmi_percent']}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exercise the current Prompt Flow lookup path locally")
    parser.add_argument(
        "--text",
        default=os.environ.get("LOOKUP_SAMPLE_TEXT", DEFAULT_SAMPLE_TEXT),
        help="Input text used to extract the line class",
    )
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
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    extracted_line_class = extract_line_class(args.text)
    normalized_line_class = get_legacy_class_line(extracted_line_class, args.text)
    wps_query = build_wps_query(as_dict={"line_class": normalized_line_class})

    print(f"input_text: {args.text}")
    print(f"extracted_line_class: {extracted_line_class}")
    print(f"normalized_line_class: {normalized_line_class}")
    print(f"wps_query: {json.dumps(wps_query, indent=2, sort_keys=True)}")

    try:
        token = get_access_token()
        wps_docs = search_index(args.endpoint, args.api_version, token, DEFAULT_WPS_INDEX, wps_query)
        nde_docs = search_index(args.endpoint, args.api_version, token, DEFAULT_NDE_INDEX, {"search": normalized_line_class, "top": 5})
    except (subprocess.CalledProcessError, OSError, RuntimeError) as exc:
        print(f"Lookup test failed before completing search: {exc}", file=sys.stderr)
        return 1

    print_document_summary("wps-diain", wps_docs)
    print_document_summary("ndeee", nde_docs)

    if not wps_docs:
        print("No WPS documents returned", file=sys.stderr)
        return 2
    if not nde_docs:
        print("No NDE documents returned", file=sys.stderr)
        return 3

    print("Lookup harness passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))