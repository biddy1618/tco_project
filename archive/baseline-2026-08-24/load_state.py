from promptflow.core import tool

REQUIRED_FIELDS = [
    "line_class", "scope_type", 'insulation', 'heat_tracing', 'hydrogen_bake_out', 'ie_doc_no',
    'dia_in', 'existing_spring_support_reuse', "placeholders_TP",
    "spool_prefab", "has_tie_ins",
    "pump_compressor_vessel_psv_in_scope",
    "new_piping_route", "insufficient_vessel_internal_data",
    "replace_existing_equipment_diff_weight",
]

EMPTY_STATE = {k: None for k in REQUIRED_FIELDS}

@tool
def load_state(chat_history: list) -> dict:
    """Walk chat_history backwards and return the last non-empty state dict."""
    for turn in reversed(chat_history or []):
        outputs = turn.get("outputs", {}) or {}
        prev = outputs.get("merge_state")
        if isinstance(prev, dict) and prev:
            # ensure all keys exist
            merged = {**EMPTY_STATE, **prev}
            merged['existing_spring_support_reuse'] = True
            return merged
    return dict(EMPTY_STATE)