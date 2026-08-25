from promptflow.core import tool

REQUIRED = [
    "line_class", "scope_type", "placeholders_TP",
    "spool_prefab", "has_tie_ins",
    "pump_compressor_vessel_psv_in_scope",
    "new_piping_route", "insufficient_vessel_internal_data",
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

@tool
def decide(state: dict) -> dict:
    missing = [k for k in REQUIRED if state.get(k) in (None, "", [])]
    if missing:
        first = missing[0]
        answer = f"Thanks. I still need: **{first}**.\n\n{QUESTIONS[first]}"
        return {"answer": answer, "complete": False, "missing": missing}
    return {
        "answer": f"✅ All fields captured:\n```json\n{state}\n```",
        "complete": True,
        "missing": [],
    }