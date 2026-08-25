from promptflow import tool
import re

@tool
def extract_line_class(user_query: str) -> str:
    """
    Extracts line class like 150H21, 300K5D, 10000K5A from user text.
    Returns class string or empty string if not found.
    """
    if not isinstance(user_query, str):
        user_query = str(user_query)

    # Pattern: digits + letters + digits/letters (covers 150H21, 300K5D, 10000K5A, etc.)
    m = re.search(r"\b\d+[A-Z]+[0-9A-Z]*\b", user_query.upper())
    return m.group(0) if m else ""