from promptflow import tool
import json
import re


def parse_json_safely(value):
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        text = value.strip()

        # remove markdown fences if model returns them
        text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        return json.loads(text)

    raise ValueError("updated_json must be dict or JSON string")

@tool
def my_python_tool(updated_json):
    updated_json = parse_json_safely(updated_json)

    required = [
        "line_class",
        "scope_type",
        'insulation',
        'heat_tracing',
        'hydrogen_bake_out',
        'ie_doc_no',
        'dia_in',
        'existing_spring_support_reuse',
        "placeholders_TP",
        "spool_prefab",
        "has_tie_ins",
        "pump_compressor_vessel_psv_in_scope",
        "new_piping_route",
        "insufficient_vessel_internal_data",
        "replace_existing_equipment_diff_weight"
    ]

    missing = []

    for field in required:
        value = updated_json.get(field)

        if value in [None, "", "null"]:
            missing.append(field)

    return {
        "state": updated_json,
        "complete": len(missing) == 0,
        "missing": missing
    }