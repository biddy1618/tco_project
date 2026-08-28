"""Scope-field extraction from a free-text / JSON repair request.

Faithful port of the original Prompt Flow ``extraction.py`` node. The single
public entry point is :func:`build_scope_json_from_input`, which returns the
full 15-field state dict consumed downstream by validation and templating.

Note: the original imported ``pandas``/``numpy`` purely for ``pd.isna`` /
``np.nan`` inside size parsing (branches that were never reached for real
inputs). Those dependencies are dropped here with identical effective
behavior.
"""

from __future__ import annotations

import json
import re
from typing import Any, List, Optional, Tuple


# --------------------------------------------------------------------------- #
# Line class
# --------------------------------------------------------------------------- #
def extract_line_class(user_query: str) -> str:
    if not isinstance(user_query, str):
        user_query = str(user_query)

    text = user_query.upper()

    # Normalize common Cyrillic look-alikes to Latin.
    replacements = {
        "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H",
        "К": "K", "М": "M", "О": "O", "Р": "P", "Т": "T", "Х": "X",
    }
    for cyr, lat in replacements.items():
        text = text.replace(cyr, lat)

    # Case 1: explicit "line class 300C80"
    m = re.search(r"LINE\s*CLASS\s*[:\-]?\s*(\d+[A-Z]+\d*[A-Z]*)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    # Case 2: full spec, e.g. 62-0300-PHC-1001-10"-300C80-HCW5
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
            r"\b[A-Z0-9]+\.([A-Z][A-Z0-9]*)\..*?" + escaped_class,   # X60.WP.3.3009.2.150P01
            r"\bX-\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,          # X-604-WP-3009-2"-150P01
            r"\b[A-Z]+-\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,     # O-3200-FG4027-4"-300H21-NI
            r"\b\d+-\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,        # 63-9100-SL-2153-3/4"-150H22-HCW5
            r"\b\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,            # 051-TL01-1/2-150H03
        ]

        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                fluid_code = match.group(1).upper()
                break

        if fluid_code:
            break

    if normalized == "150H25":
        return "150H25 (A)" if fluid_code in ["CC", "CCS", "DCS"] else "150H25 (B)"

    if normalized == "300H21":
        return "300H21 (B)" if fluid_code == "CDM" else "300H21(A)"

    if normalized == "300H25":
        return "300H25 (B)" if fluid_code in ["CC", "CCS", "DCS"] else "300H25 (A)"

    return normalized


# --------------------------------------------------------------------------- #
# Insulation
# --------------------------------------------------------------------------- #
INSULATION_PREFIXES = (
    "HCDW",  # Heat Conservation Double Layer & Electric Tracing
    "HCW",   # Heat Conservation + Electric Tracing (single layer)
    "HCS",   # Heat Conservation + Steam Tracing
    "HC",    # Heat Conservation
    "PP",    # Personnel Protection
    "CC",    # Cold Conservation
    "AC",    # Acoustic
    "FP",    # Fire Proofing
    "NI",    # Not Insulated
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
    """Return ``(is_insulated, code)``.

    - ``(False, 'NI')`` for NI / 'uninsulated'
    - ``(True, <code>)`` for any other insulation code or 'insulated'
    - ``(None, None)`` if nothing detected
    """
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


# --------------------------------------------------------------------------- #
# Heat tracing
# --------------------------------------------------------------------------- #
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


def detect_heat_tracing(text: str):
    """Return a list of tracing types, ``False`` for explicit "no tracing", or ``None``."""
    if not text:
        return None

    found: List[str] = []
    for label, pattern in HEAT_TRACING_PATTERNS:
        if pattern.search(text):
            found.append(label)

    if found:
        return list(dict.fromkeys(found))  # dedup, preserve order

    if NO_TRACING_RE.search(text):
        return False

    return None


# --------------------------------------------------------------------------- #
# Tie-in placeholders / special service
# --------------------------------------------------------------------------- #
def extract_tp_placeholders(text: str) -> list:
    if not text:
        return []

    pattern = r'\bTP\s*-?\s*\d{1,4}(?:\s*-\s*\d{3,4})?(?:\s*/\s*\d{3})*\b'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    unique = []
    seen = set()
    for match in matches:
        cleaned = re.sub(r'\s*-\s*', '-', match)
        cleaned = re.sub(r'\s*/\s*', '/', cleaned)
        cleaned = re.sub(r'\s+', '', cleaned)
        cleaned = cleaned.upper()

        if cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique


def is_special_service(line_class: str) -> bool:
    """True for K-series, C80, or A80 families (e.g. 150C80, 600A80, 150K01)."""
    if not line_class:
        return False

    lc = line_class.upper().strip()
    core = re.sub(r'^\d+', '', lc)  # strip leading numeric prefix

    if core.startswith('K') or core.startswith('JK'):
        return True
    if core.startswith('C80') or core.startswith('A80'):
        return True
    return False


# --------------------------------------------------------------------------- #
# Scope type
# --------------------------------------------------------------------------- #
def detect_scope_type(user_input: str) -> list:
    text = user_input.lower()
    detected = set()

    patterns = {
        "Flange replacement": [
            r'\bflange\s+replacement\b',
            r'\breplacement\s+of\s+(the\s+)?(leaking\s+|damaged\s+|existing\s+)?flange\b',
            r'\breplace\s+(the\s+)?(leaking\s+|damaged\s+|existing\s+)?flange\b',
            r'\bremove\s+and\s+replace\s+(the\s+)?flange\b',
            r'\brenew\s+(the\s+)?flange\b',
            r'\bflange\s+pair\b',
            r'\breplace(?:ment)?\s+of\s+(the\s+)?flange\s+pair\b',
            r'\bin\s+kind\s+replacement\s+of\s+(the\s+)?flange\s+pair\b',
            r'\breplace\s+(the\s+)?flange\s+pair\b',
            r'\bwith\s+replacement\s+of\s+(the\s+)?flange\b',
            r'\btlr[#\s0-9,/.-]+\s+will\s+be\s+removed\s+with\s+replacement\s+of\s+(the\s+)?flange\b',
            r'\b(flange)\b.*?\b(replac(e|ed|ement|ing)|renew)\b',
            r'\b(replac(e|ed|ement|ing)|renew)\b.*?\b(flange)\b',
        ],
        "Valve replacement": [
            r'\b(replace|install|remove|renew)\s+(the\s+)?valve\b',
            r'\bvalve\s+(replacement|installation)\b',
            r'\bnew\s+valve\b',
        ],
        "Piping section replacement": [
            r'\breplace\s+(the\s+)?(leaking\s+)?pipe\b',
            r'\breplace\s+(the\s+)?piping\b',
            r'\breplace\s+(the\s+)?section\b',
            r'\breplace\s+(the\s+)?spool\b',
            r'\bcut\s+and\s+replace\b',
            r'\brenew\s+(the\s+)?piping\b',
            r'\bpiping\s+replacement\b',
            r'\breplace\s+leaking\b',
            r'\b(piping\s+)?spool\s+replacement\b',
            r'\b(replace|renew|install)\s+(the\s+)?(piping\s+)?spool\b',
            r'\bclamp\b.*?\b(repair|repairing|dismantle|dismantling|remove|removing|replace|replacing)\b|\b(repair|repairing|dismantle|dismantling|remove|removing|replace|replacing)\b.*?\bclamp\b',
            r'''\b((replac(e|ed|ing)|renew|install|repair|dismantle|remove)\b.*?\b(pip(e|ing|es|line)|spoo(l|s)|sectio(n|s)|lin(e|s))|\b(pip(e|ing|es|line)|spoo(l|s)|sectio(n|s)|lin(e|s))\b.*?\b(replac(e|ed|ing)|renew|install|repair|dismantle|remove))\b''',
        ],
        "TLR": [
            r'''\b(((replac(e|ed|ing)|renew|install|repair|dismantle|remove)\b.*?\b(clamp(s)|tlr)\b)|((clamp(s)|tlr)\b.*?\b(replac(e|ed|ing)|renew|install|repair|dismantle|remove)))\b''',
            r'''\b(((replac(e|ed|ing)|renew|install|repair|dismantle|remove)\b.*?\btlr\b)|(tlr\b.*?\b(replac(e|ed|ing)|renew|install|repair|dismantle|remove)))\b''',
            r'\bTLR\b',
            r'\btlr\b',
        ],
    }

    for scope, regex_list in patterns.items():
        for pattern in regex_list:
            if re.search(pattern, text, re.IGNORECASE):
                detected.add(scope)
                break

    # Fallbacks
    if re.search(r'\breplac(e|ed|ement)\b', text) and re.search(r'\b(pipe|piping)\b', text):
        detected.add("Piping section replacement")

    if re.search(r'\breplac(e|ed|ement)\b', text) and re.search(r'\b(elbow|elbows)\b', text):
        detected.add("Elbow replacement")

    if re.search(r'\breplac(e|ed|ement)\b', text) and re.search(r'\b(tee|tees)\b', text):
        detected.add("Tee replacement")

    if re.search(r'\b(extend|extends|extending|extended)\b', text, re.IGNORECASE) and \
            re.search(r'\b(pipe|piping|pipes)\b', text, re.IGNORECASE):
        detected.add("Pipe extension")

    return list(detected)


def detect_pump_compressor_vessel_psv_scope(user_input: str) -> bool:
    text = user_input.lower()
    keywords = [
        "pump", "compressor", "vessel", "vessel nozzle", "nozzle",
        "psv", "pressure safety valve", "relief valve",
    ]
    return any(k in text for k in keywords)


def detect_new_piping_route(user_input: str) -> bool:
    text = user_input.lower()
    keywords = [
        "new piping route", "reroute", "re-route", "new route",
        "pipe support foundation", "support foundation", "excavation",
        "surveying work", "underground utilities", "unpaved areas",
        "install new support", "new support location", "new pipe rack",
        "new underground line", "new aboveground route",
    ]
    return any(k in text for k in keywords)


def detect_replace_existing_equipment_diff_weight(user_input: str) -> bool:
    text = user_input.lower()
    keywords = [
        "different weight", "new equipment indicated on drawing",
        "replacing existing equipment", "replace existing equipment",
        "equipment of different weight", "weight of the new equipment",
        "lifting plan", "center of gravity", "load change",
        "foundation load change",
    ]
    return any(k in text for k in keywords)


# --------------------------------------------------------------------------- #
# Diameter (inches)
# --------------------------------------------------------------------------- #
_UNICODE_FRACTIONS = {
    "½": " 1/2", "¼": " 1/4", "¾": " 3/4",
    "⅓": " 1/3", "⅔": " 2/3",
    "⅛": " 1/8", "⅜": " 3/8", "⅝": " 5/8", "⅞": " 7/8",
    "⅕": " 1/5", "⅖": " 2/5", "⅗": " 3/5", "⅘": " 4/5",
    "⅙": " 1/6", "⅚": " 5/6",
}

_INCH_LIKE = ['’’', '‘‘', '’', '‘', '”', '“', '″', '′', "''", '``']


def _normalize_fractions(s: str) -> str:
    for u, a in _UNICODE_FRACTIONS.items():
        s = s.replace(u, a)
    for q in _INCH_LIKE:
        s = s.replace(q, '"')
    s = re.sub(r'(\d)\.\s*(\d+/\d+)', r'\1 \2', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def parse_size_token(token) -> Optional[float]:
    """Parse a size token to a float. Examples: '3/4'->0.75, '1 1/2'->1.5, '24'->24.0."""
    if token is None:
        return None

    s = str(token).strip()
    if not s:
        return None

    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'(\d+)\.(\d+/\d+)', r'\1 \2', s)  # 1.1/2 -> 1 1/2

    m = re.fullmatch(r'(\d+)\s+(\d+)/(\d+)', s)  # mixed fraction
    if m:
        whole, num, den = m.groups()
        return float(whole) + float(num) / float(den)

    m = re.fullmatch(r'(\d+)/(\d+)', s)  # simple fraction
    if m:
        num, den = m.groups()
        return float(num) / float(den)

    try:
        return float(s)
    except ValueError:
        return None


def extract_dia_in(text: str) -> list:
    text = str(text or "").lower()
    text = _normalize_fractions(text)

    size_pattern = r'(?:\d+\s+\d+/\d+|\d+\.\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)'

    patterns = [
        rf'diameter\s*[:=]?\s*({size_pattern})\s*(?:inches\b|inch\b|in\b|")?',
        rf'pipe\s*size\s*[:=]?\s*({size_pattern})\s*(?:inches\b|inch\b|in\b|")?',
        rf'nps\s*[:=]?\s*({size_pattern})\s*(?:inches\b|inch\b|in\b|")?',
        rf'-({size_pattern})\s*(?:"|\'\'|in\b)\s*-\s*(\d+[A-Za-z]+\d*[A-Za-z]*)(?=[\s\.,;:]|$)',
        rf'\b({size_pattern})\s*(?:"|inches\b|inch\b|in\b)',
        rf'-({size_pattern})\s*(?:"|in\b)\s*-\s*\d+[A-Za-z]+\d*',
        # TCO short line id encodes NPS without an inch mark, e.g. 051-TL01-1/2-150H03.
        # Original PF required " / in, so TC-001 left dia_in empty and the MAF port
        # asked for diameter. Tracker Run Log first output is a job pack (Nur:
        # mandatory fields are already in the deducted prompt). Parse that token.
        rf'\b\d+-[a-z][a-z0-9]*-({size_pattern})-(\d+[a-z]+\d*[a-z]*)',
    ]

    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            value = parse_size_token(m.group(1))
            if value is not None:
                return [value]

    return []


# --------------------------------------------------------------------------- #
# I&E job pack document number
# --------------------------------------------------------------------------- #
IE_DOC_PATTERN = re.compile(
    r'I\s*&\s*E\s*Job\s*Pack[\s:#-]*([A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)',
    re.IGNORECASE,
)


def extract_ie_doc_no(user_input: str):
    if not user_input:
        return False
    m = IE_DOC_PATTERN.search(user_input)
    return m.group(1).upper() if m else False


# --------------------------------------------------------------------------- #
# Input parsing + top-level builder
# --------------------------------------------------------------------------- #
def parse_plain_input(user_input: str) -> dict:
    """Parse ``Problem statement: ...`` / ``Proposed solution: ...`` text."""
    if not user_input or not isinstance(user_input, str):
        return {"problem_statement": "", "proposed_solution": ""}

    text = user_input.strip()

    problem_match = re.search(
        r'problem\s*statement\s*:\s*(.*?)(?=proposed\s*solution\s*:|$)',
        text, flags=re.IGNORECASE | re.DOTALL,
    )
    solution_match = re.search(
        r'proposed\s*solution\s*:\s*(.*)',
        text, flags=re.IGNORECASE | re.DOTALL,
    )

    problem_statement = problem_match.group(1).strip() if problem_match else ""
    proposed_solution = solution_match.group(1).strip() if solution_match else ""

    return {"problem_statement": problem_statement, "proposed_solution": proposed_solution}


def build_scope_json_from_input(user_input: str) -> dict:
    """Build the full 15-field scope state from a JSON string or plain text.

    Accepts either a JSON object ``{"problem_statement": ..., "proposed_solution": ...}``
    or plain text with ``Problem statement:`` / ``Proposed solution:`` markers.
    """
    data: Any = None
    try:
        data = json.loads(user_input) if isinstance(user_input, str) else user_input
    except Exception:
        data = None

    if not isinstance(data, dict):
        data = parse_plain_input(user_input)

    if not isinstance(data, dict):
        return {
            "error": "Input must be either valid JSON string or plain text with "
                     "'Problem statement:' and 'Proposed solution:'.",
        }

    line_class_temp = extract_line_class(user_input)
    line_class = get_legacy_class_line(line_class_temp, user_input)

    scope_type = detect_scope_type(user_input)
    insulation, _code = detect_insulation(user_input)
    heat_tracing = detect_heat_tracing(user_input)
    hydrogen_bake_out = is_special_service(line_class)
    ie_doc_no = extract_ie_doc_no(user_input)
    dia_in = extract_dia_in(user_input)
    placeholders_TP = extract_tp_placeholders(user_input)

    spool_prefab = "Piping section replacement" in scope_type

    try:
        has_tie_ins = len(placeholders_TP) > 0
    except TypeError:
        has_tie_ins = False

    pump_compressor_vessel_psv_in_scope = detect_pump_compressor_vessel_psv_scope(user_input)
    new_piping_route = detect_new_piping_route(user_input)
    insufficient_vessel_internal_data = pump_compressor_vessel_psv_in_scope
    replace_existing_equipment_diff_weight = detect_replace_existing_equipment_diff_weight(user_input)

    return {
        "line_class": line_class,
        "scope_type": scope_type,
        "insulation": insulation,
        "heat_tracing": heat_tracing,
        "hydrogen_bake_out": hydrogen_bake_out,
        "ie_doc_no": ie_doc_no,
        "dia_in": dia_in,
        "existing_spring_support_reuse": True,
        "placeholders_TP": placeholders_TP,
        "spool_prefab": spool_prefab,
        "has_tie_ins": has_tie_ins,
        "pump_compressor_vessel_psv_in_scope": pump_compressor_vessel_psv_in_scope,
        "new_piping_route": new_piping_route,
        "insufficient_vessel_internal_data": insufficient_vessel_internal_data,
        "replace_existing_equipment_diff_weight": replace_existing_equipment_diff_weight,
    }
