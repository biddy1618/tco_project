from promptflow import tool
import re


def _extract_line_class(text: str):
    m = re.search(r"\b\d+[A-Z]+[0-9A-Z]*\b", text.upper())
    return m.group(0) if m else None


def _extract_item(text: str):
    m = re.search(r"\b(pipe|valve|flange|ball|gate|gasket)\b", text, re.IGNORECASE)
    return m.group(1).upper() if m else None


def _extract_size(text: str):
    """
    Returns:
      - mode = "range" with (low, high) for "size 40-48"
      - mode = "single" with (S, S) for "size 45"
      - mode = None if no size
    """
    # 1) range like "size 40-48" or "40-48"
    m = re.search(r"\bsize\b\s*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)", text, re.IGNORECASE)
    if not m:
        m = re.search(r"(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)", text)

    if m:
        low = float(m.group(1))
        high = float(m.group(2))
        if low > high:
            low, high = high, low
        return "range", low, high

    # 2) single like "size 45"
    m = re.search(r"\bsize\b\s*(\d+\.?\d*)\b", text, re.IGNORECASE)
    if m:
        s = float(m.group(1))
        return "single", s, s

    return None, None, None


@tool
def build_search_query(user_query: str) -> dict:
    line_class = _extract_line_class(user_query)
    item = _extract_item(user_query)
    mode, low, high = _extract_size(user_query)

    filters = []

    if line_class:
        filters.append(f"LINE_CLASS eq '{line_class}'")

    if item:
        filters.append(f"ITEM_NAME eq '{item}'")

    # --- SIZE FILTERING ---
    if mode == "range":
        # overlap: low_size_1 <= high AND high_size_1 >= low
        filters.append(f"(low_size_1 le {high} and high_size_1 ge {low})")

        # OPTIONAL: if you want also range2:
        # filters.append(f"((low_size_1 le {high} and high_size_1 ge {low}) or (low_size_2 le {high} and high_size_2 ge {low}))")

    elif mode == "single":
        # point-in-range: low_size_1 <= S <= high_size_1
        s = low
        filters.append(f"(low_size_1 le {s} and high_size_1 ge {s})")

        # OPTIONAL: if you want also range2:
        # filters.append(f"((low_size_1 le {s} and high_size_1 ge {s}) or (low_size_2 le {s} and high_size_2 ge {s}))")

    # You requested: search should be the class string
    search_text = line_class if line_class else "*"

    return {
        "search": search_text,
        "queryType": "semantic",
        "semanticConfiguration": "sql-index-semantic-configuration",
        "filter": " and ".join(filters),
        "top": 50
    }