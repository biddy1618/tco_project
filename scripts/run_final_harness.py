"""Local harness for the final assembly branch of the flow.

This script uses a tiny promptflow decorator stub so the repo's existing
modules can be imported in the maf environment without installing promptflow.
It then reuses the live Azure AI Search lookup helpers and runs the real
template builder to produce a final job-pack text sample.
"""

from __future__ import annotations

import argparse
import json
import sys
import types
from pathlib import Path
from typing import Iterable


def install_promptflow_stub() -> None:
    def tool(func=None, **_kwargs):
        if func is None:
            def decorator(inner):
                return inner

            return decorator
        return func

    promptflow_module = types.ModuleType("promptflow")
    promptflow_module.tool = tool

    promptflow_core_module = types.ModuleType("promptflow.core")
    promptflow_core_module.tool = tool

    sys.modules.setdefault("promptflow", promptflow_module)
    sys.modules.setdefault("promptflow.core", promptflow_core_module)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (str(PROJECT_ROOT), str(SCRIPT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

install_promptflow_stub()

import run_lookup_harness as lookup
import template
from src.pf_jobpack.lookup import build_wps_query
from src.pf_jobpack.material import check_material_ss
from src.pf_jobpack.pwht import check_pwht_flag


DEFAULT_SAMPLE_TEXT = '63-9100-SL-2153-3/4"-150H22-HCW5'
DEFAULT_ENDPOINT = lookup.DEFAULT_ENDPOINT
DEFAULT_API_VERSION = lookup.DEFAULT_API_VERSION


DEFAULT_FACTS = {
    "line_class": "150H25 (B)",
    "scope_type": "pipeline",
    "insulation": True,
    "heat_tracing": [],
    "hydrogen_bake_out": False,
    "ie_doc_no": "I&E Job Pack 24-0001",
    "dia_in": [3.0],
    "existing_spring_support_reuse": False,
    "placeholders_TP": ["TPxx-yyy/000", "TPxx-yyy/999"],
    "spool_prefab": True,
    "has_tie_ins": True,
    "pump_compressor_vessel_psv_in_scope": False,
    "new_piping_route": False,
    "insufficient_vessel_internal_data": False,
    "replace_existing_equipment_diff_weight": False,
}


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the current template assembly branch locally")
    parser.add_argument(
        "--text",
        default=DEFAULT_SAMPLE_TEXT,
        help="Sample input used to drive the lookup branch",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help="Azure AI Search endpoint",
    )
    parser.add_argument(
        "--api-version",
        default=DEFAULT_API_VERSION,
        help="Azure AI Search REST API version",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    extracted_line_class = lookup.extract_line_class(args.text)
    normalized_line_class = lookup.get_legacy_class_line(extracted_line_class, args.text)
    wps_query = build_wps_query(as_dict={"line_class": normalized_line_class})

    token = lookup.get_access_token()
    wps_docs = lookup.search_index(args.endpoint, args.api_version, token, lookup.DEFAULT_WPS_INDEX, wps_query)
    nde_docs = lookup.search_index(args.endpoint, args.api_version, token, lookup.DEFAULT_NDE_INDEX, {"search": normalized_line_class, "top": 5})

    wps_result = check_pwht_flag({"value": wps_docs}, normalized_line_class)

    if nde_docs:
        nde_result = check_material_ss([{"metadata": {"content": nde_docs[0].get("content", "")}}])
    else:
        nde_result = "No"

    final_text = template.build_job_pack(
        facts=dict(DEFAULT_FACTS),
        nde_result=nde_result,
        wps_result=wps_result,
        material=nde_result,
    )

    print(f"input_text: {args.text}")
    print(f"extracted_line_class: {extracted_line_class}")
    print(f"normalized_line_class: {normalized_line_class}")
    print(f"wps_result: {wps_result}")
    print(f"nde_result: {nde_result}")
    print("final_text_preview:")
    if isinstance(final_text, dict):
        print(json.dumps(final_text, indent=2, ensure_ascii=False))
    else:
        print(final_text)

    if not final_text:
        print("Final assembly produced an empty result", file=sys.stderr)
        return 1

    if isinstance(final_text, dict):
        payload = final_text.get("final_text", "")
    else:
        payload = final_text

    if not isinstance(payload, str) or not payload.strip():
        print("Final assembly did not produce usable text", file=sys.stderr)
        return 2

    print("Final assembly harness passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))