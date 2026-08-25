from promptflow import tool
import re

@tool
def extract_line_class(user_query: str) -> str:
    if not isinstance(user_query, str):
        user_query = str(user_query)

    text = user_query.upper()

    replacements = {
        "А": "A",
        "В": "B",
        "С": "C",
        "Е": "E",
        "Н": "H",
        "К": "K",
        "М": "M",
        "О": "O",
        "Р": "P",
        "Т": "T",
        "Х": "X",
    }

    for cyr, lat in replacements.items():
        text = text.replace(cyr, lat)

    # Case 1: explicit "line class 300C80"
    m = re.search(r"LINE\s*CLASS\s*[:\-]?\s*(\d+[A-Z]+\d*[A-Z]*)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    # Case 2: pattern like 62-0300-PHC-1001-10"-300C80-HCW5
    m = re.search(r'\d{2}-\d{4}-[A-Z0-9\-]+-\d{4}-\d{1,2}"?\s*-\s*(\d+[A-Z]+\d*[A-Z]*)\s*-[A-Z0-9]+', text, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    m = re.search(r'-(\d+[A-Z]+\d*[A-Z]*)(?=[\s\.,;:]|$)', text, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    m = re.search(r'-(\d+[A-Z]+\d*[A-Z]*)(?=-|\s|[\.,;:]|$)', text, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    
    # Final fallback (covers -, ., space, unicode mess)
    m = re.search(r'(?<![A-Z0-9])(\d+[A-Z]+\d*[A-Z]*)(?=[\s\-\.,]|$)', text)
    if m:
        return m.group(1)

    return ""