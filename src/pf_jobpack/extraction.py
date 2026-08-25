"""Pure extraction and normalization helpers for the job-pack flow."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple


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

    match = re.search(r"LINE\s*CLASS\s*[:\-]?\s*(\d+[A-Z]+\d*[A-Z]*)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r'\d{2}-\d{4}-[A-Z0-9\-]+-\d{4}-\d{1,2}"?\s*-\s*(\d+[A-Z]+\d*[A-Z]*)\s*-[A-Z0-9]+', text, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r'-(\d+[A-Z]+\d*[A-Z]*)(?=[\s\.,;:]|$)', text, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r'-(\d+[A-Z]+\d*[A-Z]*)(?=-|\s|[\.,;:]|$)', text, flags=re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r'(?<![A-Z0-9])(\d+[A-Z]+\d*[A-Z]*)(?=[\s\-\.,]|$)', text)
    if match:
        return match.group(1)

    return ""


def get_legacy_class_line(line_class: str, input_text: str) -> str:
    replacements = {
        "150H22": "150H25",
        "150H03": "150H25",
        "150K01": "150K21",
        "150P01": "150P21",
        "300H03": "300H25",
        "900H22": "900H21",
    }

    original_line_class = str(line_class).strip()
    normalized = replacements.get(original_line_class, original_line_class)

    text = str(input_text)

    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)

    text = text.replace("''", '"')
    text = text.replace("’’", '"')
    text = text.replace("”", '"')
    text = text.replace("“", '"')
    text = text.replace("½", "1/2")
    text = text.replace("¼", "1/4")
    text = text.replace("¾", "3/4")

    fluid_code = None
    classes_to_search = [original_line_class, normalized]

    for class_value in classes_to_search:
        if not class_value:
            continue

        escaped_class = re.escape(class_value)
        patterns = [
            r"\b[A-Z0-9]+\.([A-Z][A-Z0-9]*)\..*?" + escaped_class,
            r"\bX-\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,
            r"\b[A-Z]+-\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,
            r"\b\d+-\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,
            r"\b\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                fluid_code = match.group(1).upper()
                break

        if fluid_code:
            break

    if normalized == "150H25":
        if fluid_code in ["CC", "CCS", "DCS"]:
            return "150H25 (A)"
        return "150H25 (B)"

    if normalized == "300H21":
        if fluid_code == "CDM":
            return "300H21 (B)"
        return "300H21(A)"

    if normalized == "300H25":
        if fluid_code in ["CC", "CCS", "DCS"]:
            return "300H25 (B)"
        return "300H25 (A)"

    return normalized


INSULATION_PREFIXES = (
    "HCDW",
    "HCW",
    "HCS",
    "HC",
    "PP",
    "CC",
    "AC",
    "FP",
    "NI",
)

INSULATION_TAIL_RE = re.compile(
    r"-(" + "|".join(INSULATION_PREFIXES) + r")(\d*)\b",
    re.IGNORECASE,
)

UNINSULATED_RE = re.compile(r"\b(un[-\s]?insulated|not\s+insulated|no\s+insulation)\b", re.IGNORECASE)
INSULATED_RE = re.compile(r"\binsulated\b", re.IGNORECASE)


def extract_insulation_code(text: str) -> Optional[str]:
    """Return the insulation code found in a line number (e.g. 'HCW5', 'NI'), or None."""
    if not text:
        return None
    matches = list(INSULATION_TAIL_RE.finditer(text))
    if not matches:
        return None
    prefix, digits = matches[-1].groups()
    return (prefix + digits).upper()


def detect_insulation(text: str) -> Tuple[Optional[bool], Optional[str]]:
    if not text:
        return (None, None)

    code = extract_insulation_code(text)
    if code == "NI":
        return (False, "NI")
    if code:
        return (True, code)

    if UNINSULATED_RE.search(text):
        return (False, None)
    if INSULATED_RE.search(text):
        return (True, None)

    return (None, None)


HEAT_TRACING_PATTERNS = [
    ("contro-trace", re.compile(r"\bcontro?l[-\s]?trace(?:d|ing)?\b", re.IGNORECASE)),
    ("electric", re.compile(r"\belectric(?:al)?\s+(?:heat\s+)?trac(?:ing|ed|e)\b", re.IGNORECASE)),
    ("steam", re.compile(r"\bsteam\s+(?:heat\s+)?trac(?:ing|ed|e)\b", re.IGNORECASE)),
    ("water", re.compile(r"\b(?:hot\s+)?water\s+(?:heat\s+)?trac(?:ing|ed|e)\b", re.IGNORECASE)),
]

NO_TRACING_RE = re.compile(
    r"\b(?:no|without|not)\s+heat\s+trac(?:ing|ed|e)\b"
    r"|\bnot\s+trac(?:ed|ing)\b"
    r"|\bno\s+tracing\b",
    re.IGNORECASE,
)


def detect_heat_tracing(text: str) -> Optional[List[str]]:
    if not text:
        return None

    found: List[str] = []
    for label, pattern in HEAT_TRACING_PATTERNS:
        if pattern.search(text):
            found.append(label)

    if found:
        return list(dict.fromkeys(found))

    if NO_TRACING_RE.search(text):
        return False

    return None


NO_TIEIN_PATTERNS = [
    r'\bN\s*/\s*A\s+Tie[-\s]?ins?\b',
    r'\bTie[-\s]?ins?\s+at\s*\[?\s*tie[-\s]?in\s+IDs?\s+TBD\s*\]?',
    r'\bNo\s+TP(?:s)?\b',
    r'\bNo\s+Tie[-\s]?ins?\b',
    r'\bTBD\b.*\btie[-\s]?ins?\b',
]


def is_special_service(line_class: str) -> bool:
    """Return True for K-series, C80, or A80 families."""
    text = str(line_class).upper()
    return bool(re.search(r"\b\d+(?:K|C80|A80)", text))


def build_wps_query(as_string: str = "", as_dict: Optional[dict] = None) -> dict | str:
    as_dict = as_dict or {}

    line_class = ""
    dia_in: List[object] = []

    if as_string and str(as_string).strip():
        return as_string

    try:
        line_class = (as_dict.get("line_class") or "").strip()  # type: ignore[union-attr]
    except Exception:
        pass

    try:
        raw = as_dict.get("dia_in")  # type: ignore[union-attr]
        if isinstance(raw, list):
            dia_in = raw
    except Exception:
        pass

    filters = []
    if len(dia_in):
        value = dia_in[-1]
        filters.append(f"dia_in1 le {value} and dia_in2 ge {value}")

    return {
        "search": line_class if line_class else "*",
        "queryType": "semantic",
        "semanticConfiguration": "wps-diain-semantic-configuration",
        "filter": " and ".join(filters) if filters else "",
        "top": 6,
    }