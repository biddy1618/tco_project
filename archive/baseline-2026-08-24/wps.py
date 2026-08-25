from promptflow import tool

from typing import Dict, Any
import pandas as pd
import re

@tool
def my_python_tool(line_class: str, user_query) -> Dict[str, Any]:
    filters = []

    line_class = (line_class or "").strip()

    # Handle user_query as dict or string
    # if isinstance(user_query, dict):
    #     problem_statement = str(user_query.get("problem_statement", "") or "").strip()
    #     proposed_solution = str(user_query.get("proposed_solution", "") or "").strip()
    #     query_text = f"{problem_statement} {proposed_solution}".strip()
    # else:
    #     query_text = str(user_query or "").strip()

    dia_in = extract_dia_in(user_query)

    # build thickness filter
    if len(dia_in) == 1:
        value = dia_in[0]
        filters.append(f"dia_in1 le {value} and dia_in2 ge {value}")

    return {
        "search": line_class if line_class else "*",
        "queryType": "semantic",
        "semanticConfiguration": "wps-diain-semantic-configuration",
        "filter": "".join(filters) if filters else "",
        "top": 6,
    }

def parse_size_token(token):
    """
    Examples:
    '1/2'     -> 0.5
    '3/4'     -> 0.75
    '1 1/2'   -> 1.5
    '1.1/2'   -> 1.5
    '24'      -> 24.0
    """
    if pd.isna(token):
        return np.nan

    s = str(token).strip()
    if not s:
        return np.nan

    # normalize spaces
    s = re.sub(r'\s+', ' ', s)

    # convert 1.1/2 -> 1 1/2
    s = re.sub(r'(\d+)\.(\d+/\d+)', r'\1 \2', s)

    # mixed fraction: 1 1/2
    m = re.fullmatch(r'(\d+)\s+(\d+)/(\d+)', s)
    if m:
        whole, num, den = m.groups()
        return float(whole) + float(num) / float(den)

    # simple fraction: 3/4
    m = re.fullmatch(r'(\d+)/(\d+)', s)
    if m:
        num, den = m.groups()
        return float(num) / float(den)

    # normal number
    try:
        return float(s)
    except ValueError:
        return None


def extract_dia_in(text: str):
    text = str(text or "").lower()


    # size token pattern:
    # 1 1/2
    # 1.1/2
    # 1/2
    # 10
    #size_pattern = r"(\d+\s+\d+/\d+|\d+\.\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)"
    size_pattern = r'(?:\d+\s+\d+/\d+|\d+\.\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)'

    patterns = [
        # 1) explicit diameter ... in or "
        rf'diameter\s*[:=]?\s*({size_pattern})\s*(?:in\b|")',

        # 2) explicit pipe size ... "
        rf'pipe\s*size\s*[:=]?\s*({size_pattern})\s*(?:in\b|")',

        # 3) NPS 1/2"
        rf'nps\s*[:=]?\s*({size_pattern})\s*(?:in\b|")',

        # 4) spec format like 62-0300-PHC-1001-1/2"-300C80-HCW5
        rf'-({size_pattern})"?\s*-\s*(\d+[A-Z]+\d*[A-Z]*)(?=[\s\.,;:]|$)',

        # 5) generic standalone quoted size like 10"-pipe size
        rf'\b({size_pattern})"',

        rf'-({size_pattern})["\']*\s*-\s*\d+[A-Z]+\d*'

    ]

    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            value = parse_size_token(m.group(1))
            if value is not None:
                return [value]

    return []

