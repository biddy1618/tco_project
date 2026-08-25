from promptflow import tool
from typing import Any, Dict, Union
import json
import ast

@tool
def route_prev(prev: Any) -> Dict[str, Any]:
    """
    Detects whether prev node output is a dict (JSON) or a plain string.
    Returns a routing signal + normalized payload for downstream nodes.
    """
    kind = "string"
    payload_dict: Dict[str, Any] = {}
    payload_str: str = ""

    # If upstream sent a JSON string, try to parse it first
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
        "kind": kind,              # "json" or "string"
        "as_dict": payload_dict,   # used when kind == "json"
        "as_string": payload_str,  # used when kind == "string"
    }