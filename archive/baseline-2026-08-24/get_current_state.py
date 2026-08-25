from promptflow import tool
import json


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
    "replace_existing_equipment_diff_weight": None
}


@tool
def get_current_state(chat_history) -> dict:
    """
    Get latest state from chat_history.
    If no previous state exists, return default empty state.
    """

    if not chat_history:
        return DEFAULT_STATE

    # Search from latest message backwards
    for item in reversed(chat_history):
        outputs = item.get("outputs", {}) if isinstance(item, dict) else {}

        # Option 1: state saved directly in outputs
        if "state" in outputs and outputs["state"]:
            state = outputs["state"]

            if isinstance(state, str):
                try:
                    state = json.loads(state)
                except Exception:
                    continue

            if isinstance(state, dict):
                return state

        # Option 2: validation output saved in outputs
        if "validation" in outputs and outputs["validation"]:
            validation = outputs["validation"]

            if isinstance(validation, str):
                try:
                    validation = json.loads(validation)
                except Exception:
                    continue

            if isinstance(validation, dict) and "state" in validation:
                return validation["state"]

    return DEFAULT_STATE