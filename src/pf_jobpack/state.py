"""State validation and routing helpers for the job-pack flow."""

from __future__ import annotations

import ast
import json
from typing import Any, Dict


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

CORRECTABLE_FIELDS = {"line_class", "scope_type", "ie_doc_no", "dia_in", "heat_tracing"}


def parse_json_safely(value: object) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        text = value.strip()

        cleaned = text
        cleaned = cleaned.removeprefix("```json").strip()
        cleaned = cleaned.removeprefix("```").strip()
        cleaned = cleaned.removesuffix("```").strip()

        try:
            parsed = json.loads(cleaned)
        except Exception:
            parsed = ast.literal_eval(cleaned)

        if isinstance(parsed, dict):
            return parsed

    raise ValueError("updated_json must be dict or JSON string")


def validate_state(updated_json: object) -> Dict[str, Any]:
    state = parse_json_safely(updated_json)

    missing = []
    for field in REQUIRED_FIELDS:
        value = state.get(field)
        if value in [None, "", "null"]:
            missing.append(field)

    return {
        "state": state,
        "complete": len(missing) == 0,
        "missing": missing,
    }


def route_prev(prev: Any) -> Dict[str, Any]:
    kind = "string"
    payload_dict: Dict[str, Any] = {}
    payload_str: str = ""

    if isinstance(prev, str):
        parsed = None
        try:
            parsed = json.loads(prev)
        except Exception:
            pass

        if parsed is None:
            try:
                parsed = ast.literal_eval(prev)
            except Exception:
                pass

        if isinstance(parsed, dict):
            prev = parsed

    if isinstance(prev, dict):
        kind = "json"
        payload_dict = prev
    elif isinstance(prev, str):
        kind = "string"
        payload_str = prev.strip()

    return {
        "kind": kind,
        "as_dict": payload_dict,
        "as_string": payload_str,
    }


EMPTY_STATE = {k: None for k in REQUIRED_FIELDS}


def load_state(chat_history: list) -> Dict[str, Any]:
    for turn in reversed(chat_history or []):
        outputs = turn.get("outputs", {}) or {}
        prev = outputs.get("merge_state")
        if isinstance(prev, dict) and prev:
            merged = {**EMPTY_STATE, **prev}
            merged["existing_spring_support_reuse"] = True
            return merged
    return dict(EMPTY_STATE)


def _is_empty(value: object) -> bool:
    return value is None or value == "" or value == [] or value == {}


def merge_state(prev_state: dict, new_extraction: dict) -> dict:
    merged = dict(prev_state or {})

    for key, value in (new_extraction or {}).items():
        if _is_empty(value):
            continue

        prev = merged.get(key)

        if isinstance(value, list) and isinstance(prev, list):
            merged[key] = list(dict.fromkeys([*prev, *value]))
            continue

        if isinstance(value, bool):
            if isinstance(prev, bool):
                merged[key] = prev or value
            else:
                merged[key] = value
            continue

        if not _is_empty(prev) and key not in CORRECTABLE_FIELDS:
            continue

        merged[key] = value

    return merged