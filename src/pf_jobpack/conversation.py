"""Conversation state and summary helpers."""

from __future__ import annotations

import json


REQUIRED = [
    "line_class",
    "scope_type",
    "placeholders_TP",
    "spool_prefab",
    "has_tie_ins",
    "pump_compressor_vessel_psv_in_scope",
    "new_piping_route",
    "insufficient_vessel_internal_data",
    "replace_existing_equipment_diff_weight",
]

QUESTIONS = {
    "line_class": "What is the line class (e.g., 300H21)?",
    "scope_type": "What is the scope of work (e.g., TLR, Pipe extension)?",
    "placeholders_TP": "Please provide the TP placeholders (e.g., TP-001).",
    "spool_prefab": "Is spool prefabrication required? (yes/no)",
    "has_tie_ins": "Are there any tie-ins involved? (yes/no)",
    "pump_compressor_vessel_psv_in_scope": "Is any pump / compressor / vessel / PSV in scope? (yes/no)",
    "new_piping_route": "Is a new piping route required? (yes/no)",
    "insufficient_vessel_internal_data": "Is vessel internal data insufficient? (yes/no)",
    "replace_existing_equipment_diff_weight": "Will equipment of different weight replace existing? (yes/no)",
}


def decide(state: dict) -> dict:
    missing = [key for key in REQUIRED if state.get(key) in (None, "", [])]
    if missing:
        first = missing[0]
        answer = f"Thanks. I still need: **{first}**.\n\n{QUESTIONS[first]}"
        return {"answer": answer, "complete": False, "missing": missing}

    return {
        "answer": f"✅ All fields captured:\n```json\n{state}\n```",
        "complete": True,
        "missing": [],
    }


DEFAULT_STATE = {
    "line_class": None,
    "scope_type": None,
    "placeholders_TP": None,
    "spool_prefab": None,
    "has_tie_ins": None,
    "insulation": None,
    "heat_tracing": None,
    "destruct_no": None,
    "construct_no": None,
    "pump_compressor_vessel_psv_in_scope": None,
    "new_piping_route": None,
    "insufficient_vessel_internal_data": None,
    "replace_existing_equipment_diff_weight": None,
}


def get_current_state(chat_history) -> dict:
    if not chat_history:
        return dict(DEFAULT_STATE)

    for item in reversed(chat_history):
        outputs = item.get("outputs", {}) if isinstance(item, dict) else {}

        if "state" in outputs and outputs["state"]:
            state = outputs["state"]

            if isinstance(state, str):
                try:
                    state = json.loads(state)
                except Exception:
                    continue

            if isinstance(state, dict):
                return state

        if "validation" in outputs and outputs["validation"]:
            validation = outputs["validation"]

            if isinstance(validation, str):
                try:
                    validation = json.loads(validation)
                except Exception:
                    continue

            if isinstance(validation, dict) and "state" in validation:
                return validation["state"]

    return dict(DEFAULT_STATE)


def merge_outputs(left_result, right_result) -> str:
    def to_text(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)

    left_text = to_text(left_result)
    right_text = to_text(right_result)

    md = []
    md.append("## Scenario A (Class extraction / lookup)")
    md.append(left_text if left_text else "No output from Scenario A.")
    md.append("")
    md.append("## Scenario B (Filtered material list by size)")
    md.append(right_text if right_text else "No output from Scenario B.")

    return "\n".join(md)