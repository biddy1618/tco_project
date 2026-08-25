from promptflow import tool
from typing import List, Dict, Any
import re

@tool
def check_material_ss(search_output: List[Dict[str, Any]]) -> str:
    if not search_output:
        return "No"

    first_item = search_output[0]

    content = ""

    # Case 1: metadata is dict and contains content
    metadata = first_item.get("metadata")
    if isinstance(metadata, dict):
        content = metadata.get("content", "")

    # Case 2: metadata is int, content is in additional_fields
    elif isinstance(metadata, int):
        additional_fields = first_item.get("additional_fields", {})
        if isinstance(additional_fields, dict):
            content = additional_fields.get("content", "")

    if not isinstance(content, str) or not content.strip():
        return "No"

    # Extract material text after the word "Material"
    match = re.search(r"Material\s+(.+?)(?:\.|$)", content, re.IGNORECASE)
    
    if not match:
        return "No"
    else:
        material_text = match.group(1).strip()

    # ✅ strict match: only CS or LTCS (optionally spaces)
        if re.fullmatch(r'(LTCS NACE|LTCS|CS)', material_text.strip().upper()):
            return "CS"
        elif re.search(r'\bSS\b', material_text.upper()):
            return "SS"
        else:
            return 'Null'