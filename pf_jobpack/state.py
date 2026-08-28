"""Conversation state handling: load, merge, validate, and route.

Faithful port of the original Prompt Flow ``load_state.py``, ``mege_state.py``,
``validation.py``, and ``router.py`` nodes.
"""

from __future__ import annotations

import ast
import json
import re
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

EMPTY_STATE = {k: None for k in REQUIRED_FIELDS}

# Fields the user can legitimately correct in a later turn (non-bool).
CORRECTABLE_FIELDS = {"line_class", "scope_type", "ie_doc_no", "dia_in", "heat_tracing"}


# --------------------------------------------------------------------------- #
# load_state
# --------------------------------------------------------------------------- #
def load_state(chat_history: list) -> Dict[str, Any]:
    """Walk chat_history backwards and return the last non-empty merged state."""
    for turn in reversed(chat_history or []):
        outputs = turn.get("outputs", {}) or {}
        prev = outputs.get("merge_state")
        if isinstance(prev, dict) and prev:
            merged = {**EMPTY_STATE, **prev}
            merged["existing_spring_support_reuse"] = True
            return merged
    return dict(EMPTY_STATE)


# --------------------------------------------------------------------------- #
# merge_state
# --------------------------------------------------------------------------- #
def _is_empty(v) -> bool:
    """True if the value carries no information (should NOT overwrite anything)."""
    return v is None or v == "" or v == [] or v == {}


def merge_state(prev_state: dict, new_extraction: dict) -> dict:
    """Merge rules:

    1. Empty new values (None/""/[]/{}) never overwrite anything.
    2. Lists are unioned (order-preserving, dedup).
    3. Booleans are monotonic: once True, stays True. False can be promoted to
       True, but True is never downgraded to False.
    4. Sticky: otherwise keep prev unless the field is in ``CORRECTABLE_FIELDS``.
    """
    merged = dict(prev_state or {})

    for k, v in (new_extraction or {}).items():
        if _is_empty(v):
            continue

        prev = merged.get(k)

        if isinstance(v, list) and isinstance(prev, list):
            merged[k] = list(dict.fromkeys([*prev, *v]))
            continue

        if isinstance(v, bool):
            if isinstance(prev, bool):
                merged[k] = prev or v
            else:
                merged[k] = v
            continue

        if not _is_empty(prev) and k not in CORRECTABLE_FIELDS:
            continue

        merged[k] = v

    # Extraction returns [] when no TPs are in the text. Merge used to leave
    # EMPTY_STATE's null, and validation treated null as missing — so Tracker
    # prompts with "[tie-in IDs TBD]" asked for TPs. ID003 still emitted a pack
    # and skipped TP-specific site lines. [] is already "present" for validate.
    if merged.get("placeholders_TP") is None:
        merged["placeholders_TP"] = []

    return merged


# --------------------------------------------------------------------------- #
# validate_state
# --------------------------------------------------------------------------- #
def parse_json_safely(value) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        text = value.strip()
        # remove markdown fences if the model returned them
        text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    raise ValueError("updated_json must be dict or JSON string")


def validate_state(updated_json) -> Dict[str, Any]:
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


# --------------------------------------------------------------------------- #
# route_prev
# --------------------------------------------------------------------------- #
def route_prev(prev: Any) -> Dict[str, Any]:
    """Normalize the ask/finalize output into a routing signal + payload.

    Returns ``kind`` ("json" or "string"), plus ``as_dict`` / ``as_string``.
    """
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
