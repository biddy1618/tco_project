"""Local harness for the validation and routing branch of the flow.

This script mirrors the current Prompt Flow behavior enough to test the state
transition locally without depending on promptflow packages.

It checks required fields, reports missing values, and shows the message that
the ask/finalize prompt would receive.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


REQUIRED_FIELDS = [
    "line_class",
    "scope_type",
    "insulation",
    "heat_tracing",
    "hydrogen_bake_out",
    "ie_doc_no",
    "dia_in",
    "existing_spring_support_reuse",
    "placeholders_TP",
    "spool_prefab",
    "has_tie_ins",
    "pump_compressor_vessel_psv_in_scope",
    "new_piping_route",
    "insufficient_vessel_internal_data",
    "replace_existing_equipment_diff_weight",
]


DEFAULT_STATE = {
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

ELECTRIC_STATE = {
    **DEFAULT_STATE,
    "heat_tracing": ["electric"],
    "ie_doc_no": "",
}

MISSING_IE_DOC_STATE = {
    **DEFAULT_STATE,
    "ie_doc_no": "",
}


def validate_state(updated_json: dict[str, object]) -> dict[str, object]:
    missing = []
    for field in REQUIRED_FIELDS:
        value = updated_json.get(field)
        if value in [None, "", "null"]:
            missing.append(field)

    return {
        "state": updated_json,
        "complete": len(missing) == 0,
        "missing": missing,
    }


def route_prev(prev: object) -> dict[str, object]:
    if isinstance(prev, dict):
        return {
            "kind": "json",
            "as_dict": prev,
            "as_string": "",
        }

    if isinstance(prev, str):
        text = prev.strip()
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return {
                    "kind": "json",
                    "as_dict": parsed,
                    "as_string": "",
                }
        except Exception:
            pass

        return {
            "kind": "string",
            "as_dict": {},
            "as_string": text,
        }

    return {
        "kind": "string",
        "as_dict": {},
        "as_string": str(prev).strip(),
    }


def render_ask_or_finalize(state: dict[str, object], complete: bool, missing: list[str]) -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "ask_or_finalize.jinja2"
    template = prompt_path.read_text(encoding="utf-8")
    return (
        template.replace("{{state}}", json.dumps(state, indent=2, ensure_ascii=False))
        .replace("{{complete}}", json.dumps(complete))
        .replace("{{missing}}", json.dumps(missing, indent=2, ensure_ascii=False))
    )


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exercise the validation/routing branch locally")
    parser.add_argument(
        "--scenario",
        choices=("complete", "missing-ie-doc", "electric"),
        default="complete",
        help="Prebuilt sample state to run",
    )
    parser.add_argument(
        "--state",
        default="",
        help="Optional JSON string to validate instead of the built-in sample state",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    if args.state.strip():
        try:
            state = json.loads(args.state)
        except json.JSONDecodeError as exc:
            print(f"Invalid JSON supplied to --state: {exc}", file=sys.stderr)
            return 1
    else:
        if args.scenario == "missing-ie-doc":
            state = dict(MISSING_IE_DOC_STATE)
        elif args.scenario == "electric":
            state = dict(ELECTRIC_STATE)
        else:
            state = dict(DEFAULT_STATE)

    validation = validate_state(state)
    routing = route_prev(validation)
    prompt_preview = render_ask_or_finalize(validation["state"], validation["complete"], validation["missing"])

    print(f"complete: {validation['complete']}")
    print(f"missing: {', '.join(validation['missing']) if validation['missing'] else '(none)'}")
    print(f"route.kind: {routing['kind']}")
    print("ask_or_finalize_preview:")
    print(prompt_preview)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))