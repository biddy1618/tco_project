"""Material classification (CS / SS / Null).

Faithful port of the original ``material.py`` node.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def check_material_ss(search_output: List[Dict[str, Any]]) -> str:
    if not search_output:
        return "No"

    first_item = search_output[0]
    content = ""

    metadata = first_item.get("metadata")
    if isinstance(metadata, dict):
        content = metadata.get("content", "")
    elif isinstance(metadata, int):
        additional_fields = first_item.get("additional_fields", {})
        if isinstance(additional_fields, dict):
            content = additional_fields.get("content", "")

    if not isinstance(content, str) or not content.strip():
        return "No"

    match = re.search(r"Material\s+(.+?)(?:\.|$)", content, re.IGNORECASE)
    if not match:
        return "No"

    material_text = match.group(1).strip()

    if re.fullmatch(r'(LTCS NACE|LTCS|CS)', material_text.strip().upper()):
        return "CS"
    if re.search(r'\bSS\b', material_text.upper()):
        return "SS"
    return "Null"
