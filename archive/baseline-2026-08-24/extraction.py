from promptflow import tool
import re
import json
from typing import Optional, Tuple, List, Any
import pandas as pd

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
            # Dot format: X60.WP.3.3009.2.150P01
            r"\b[A-Z0-9]+\.([A-Z][A-Z0-9]*)\..*?" + escaped_class,

            # X format: X-604-WP-3009-2"-150P01
            r"\bX-\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,

            # Prefix format: O-3200-FG4027-4"-300H21-NI
            r"\b[A-Z]+-\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,

            # Two number format: 63-9100-SL-2153-3/4"-150H22-HCW5
            r"\b\d+-\d+-([A-Z][A-Z0-9]*)-.*?" + escaped_class,

            # Standard format: 051-TL01-1/2-150H03
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

# Known insulation code prefixes (extend as needed)
INSULATION_PREFIXES = (
    "HCDW",   # Heat Conservation Double Layer & Electric Tracing
    "HCW",    # Heat Conservation + Electric Tracing (single layer)
    "HCS",    # Heat Conservation + Steam Tracing (common variant)
    "HC",     # Heat Conservation
    "PP",     # Personnel Protection
    "CC",     # Cold Conservation
    "AC",     # Acoustic
    "FP",     # Fire Proofing
    "NI",     # Not Insulated
)

# Matches the tail insulation token in a line number, e.g.
#   ...-150H22-HCW5   ...-150H03-NI   ...-300H21-HCDW10
INSULATION_TAIL_RE = re.compile(
    r"-(" + "|".join(INSULATION_PREFIXES) + r")(\d*)\b",
    re.IGNORECASE,
)

# Free-text keywords
UNINSULATED_RE = re.compile(r"\b(un[-\s]?insulated|not\s+insulated|no\s+insulation)\b", re.IGNORECASE)
INSULATED_RE   = re.compile(r"\binsulated\b", re.IGNORECASE)


def extract_insulation_code(text: str) -> Optional:
    """Return the insulation code found in a line number (e.g. 'HCW5', 'NI'), or None."""
    if not text:
        return None
    # scan all matches, keep the LAST one (line-number tail)
    matches = list(INSULATION_TAIL_RE.finditer(text))
    if not matches:
        return None
    prefix, digits = matches[-1].groups()
    return (prefix + digits).upper()


def detect_insulation(text: str) -> Tuple[Optional[bool], Optional[str]]:
    """
    Returns (is_insulated, code):
      - (False, 'NI')     if code is NI, or prompt says 'uninsulated/not insulated'
      - (True,  <code>)   if any other insulation code is found, or prompt says 'insulated'
      - (None,  None)     if nothing detected
    """
    if not text:
        return (None, None)

    code = extract_insulation_code(text)

    # Rule 1: explicit code from line number wins
    if code == "NI":
        return (False, "NI")
    if code:
        return (True, code)

    # Rule 2: fall back to free-text keywords
    if UNINSULATED_RE.search(text):     # check "uninsulated" BEFORE "insulated"
        return (False, None)
    if INSULATED_RE.search(text):
        return (True, None)

    # Rule 3: not mentioned
    return (None, None)

# ---------- Vocabulary ----------
# Order matters: more specific patterns first (control-trace before generic "trace")
HEAT_TRACING_PATTERNS = [
    ("contro-trace", re.compile(r"\bcontro?l[-\s]?trace(?:d|ing)?\b", re.IGNORECASE)),
    ("electric",      re.compile(r"\belectric(?:al)?\s+(?:heat\s+)?trac(?:ing|ed|e)\b", re.IGNORECASE)),
    ("steam",         re.compile(r"\bsteam\s+(?:heat\s+)?trac(?:ing|ed|e)\b", re.IGNORECASE)),
    ("water",         re.compile(r"\b(?:hot\s+)?water\s+(?:heat\s+)?trac(?:ing|ed|e)\b", re.IGNORECASE)),
]

# Explicit "no tracing"
NO_TRACING_RE = re.compile(
    r"\b(?:no|without|not)\s+heat\s+trac(?:ing|ed|e)\b"
    r"|\bnot\s+trac(?:ed|ing)\b"
    r"|\bno\s+tracing\b",
    re.IGNORECASE,
)


def detect_heat_tracing(text: str) -> Optional[List[str]]:
    """
    Returns:
      - list of tracing types found, e.g. ["electric"], ["steam", "electric"]
      - []   if explicitly stated "no heat tracing"
      - None if not mentioned / TBD / unknown
    """
    if not text:
        return None

    found: List[str] = []

    # 1) Free-text keyword scan
    for label, pattern in HEAT_TRACING_PATTERNS:
        if pattern.search(text):
            found.append(label)

    if found:
        return list(dict.fromkeys(found))   # dedup, preserve order

    # 2) Explicit "no heat tracing"
    if NO_TRACING_RE.search(text):
        return False

    # 3) TBD or not mentioned
    return None  

# Phrases that explicitly indicate there are NO tie-ins / TPs
NO_TIEIN_PATTERNS = [
    r'\bN\s*/\s*A\s+Tie[-\s]?ins?\b', # N/A Tie-ins, N/A Tie in
    r'\bTie[-\s]?ins?\s+at\s*\[?\s*tie[-\s]?in\s+IDs?\s+TBD\s*\]?', # Tie-ins at [tie-in IDs TBD]
    r'\bNo\s+TP(?:s)?\b', # No TP, No TPs
    r'\bNo\s+Tie[-\s]?ins?\b', # No Tie-ins, No Tie in
    r'\bTBD\b.*\btie[-\s]?ins?\b', # TBD ... tie-ins (loose safety net)
]

def is_special_service(line_class: str) -> bool:
    """
    Returns True if the line_class belongs to K-series, C80, or A80 family.
    Examples that return True:
        150C80, 300C80, 600A80, 600C80, 900A80, 900C80,
        150K01, 150JK0(JACKETED SYSTEM), 150K09SM(JACKETED SYSTEM),
        300K5A (AG) & (UG), 600K5H(AG) & (UG), 1500K1, 2500K1,
        10000K, 10000K5A
    """
    if not line_class:
        return False

    # Normalize: uppercase + strip whitespace
    lc = line_class.upper().strip()

    # Remove leading numeric prefix (e.g. 150, 300, 600, 900, 1500, 2500, 10000)
    # so the "letter part" is what remains
    core = re.sub(r'^\d+', '', lc)

    # Rule 1: starts with K  (covers K01, K02, K21, K5A, K09SM, JK0, etc.)
    #         also covers JK0 -> "JK0..." — handle explicitly
    if core.startswith('K') or core.startswith('JK'):
        return True

    # Rule 2: contains C80 or A80  (covers 150C80, 600A80, etc.)
    if core.startswith('C80') or core.startswith('A80'):
        return True

    return False

def extract_tp_placeholders(text: str) -> list:
    if not text:
        return []

    pattern = r'\bTP\s*-?\s*\d{1,4}(?:\s*-\s*\d{3,4})?(?:\s*/\s*\d{3})*\b'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    unique = []
    seen = set()
    for m in matches:
        # normalize spaces: TP25- 0424/001 -> TP25-0424/001
        m_clean = re.sub(r'\s*-\s*', '-', m)
        m_clean = re.sub(r'\s*/\s*', '/', m_clean)
        m_clean = re.sub(r'\s+', '', m_clean)
        m_clean = m_clean.upper()

        if m_clean not in seen:
            seen.add(m_clean)
            unique.append(m_clean)
    return unique

    if unique:
        return unique

    # Check "no tie-ins" indicators

    for pat in NO_TIEIN_PATTERNS:
        if re.search(pat, text, flags=re.IGNORECASE):
            return False

def detect_scope_type(user_input) -> str:#(problem_statement: str, proposed_solution: str) -> str:
    #text = f"{problem_statement} {proposed_solution}".lower()
    text = user_input.lower()

    my_set = set()

    
    patterns = {
        "Flange replacement": [
            # explicit direct flange replacement
            r'\bflange\s+replacement\b',
            r'\breplacement\s+of\s+(the\s+)?(leaking\s+|damaged\s+|existing\s+)?flange\b',
            r'\breplace\s+(the\s+)?(leaking\s+|damaged\s+|existing\s+)?flange\b',
            r'\bremove\s+and\s+replace\s+(the\s+)?flange\b',
            r'\brenew\s+(the\s+)?flange\b',

            # flange pair wording
            r'\bflange\s+pair\b',
            r'\breplace(?:ment)?\s+of\s+(the\s+)?flange\s+pair\b',
            r'\bin\s+kind\s+replacement\s+of\s+(the\s+)?flange\s+pair\b',
            r'\breplace\s+(the\s+)?flange\s+pair\b',

            # wording where valve/TLR removal leads explicitly to flange replacement
            r'\bwith\s+replacement\s+of\s+(the\s+)?flange\b',
            r'\btlr[#\s0-9,/.-]+\s+will\s+be\s+removed\s+with\s+replacement\s+of\s+(the\s+)?flange\b',

            # reversed word order
            r'\b(flange)\b.*?\b(replac(e|ed|ement|ing)|renew)\b',
            r'\b(replac(e|ed|ement|ing)|renew)\b.*?\b(flange)\b',
        ],

        "Valve replacement": [
            r'\b(replace|install|remove|renew)\s+(the\s+)?valve\b',
            r'\bvalve\s+(replacement|installation)\b',
            r'\bnew\s+valve\b'
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
            #r'\b(replac(e|ed|ing)|renew|install)\b.*?\b(pip(e|ing|es|line)|spoo(l|s)|sectio(n|s)|lin(e|s))\b'
            r'''\b((replac(e|ed|ing)|renew|install|repair|dismantle|remove)\b.*?\b(pip(e|ing|es|line)|spoo(l|s)|sectio(n|s)|lin(e|s))|\b(pip(e|ing|es|line)|spoo(l|s)|sectio(n|s)|lin(e|s))\b.*?\b(replac(e|ed|ing)|renew|install|repair|dismantle|remove))\b'''  # normal + reversed
        ],

        "TLR": [
            r'''\b(((replac(e|ed|ing)|renew|install|repair|dismantle|remove)\b.*?\b(clamp(s)|tlr)\b)|((clamp(s)|tlr)\b.*?\b(replac(e|ed|ing)|renew|install|repair|dismantle|remove)))\b''',
            r'''\b(((replac(e|ed|ing)|renew|install|repair|dismantle|remove)\b.*?\btlr\b)|(tlr\b.*?\b(replac(e|ed|ing)|renew|install|repair|dismantle|remove)))\b''',
            r'\bTLR\b',
            r'\btlr\b'
        ]
    }

    for scope, regex_list in patterns.items():
        for pattern in regex_list:
            if re.search(pattern, text, re.IGNORECASE):
                my_set.add(scope)
                break  # stop after first match for this scope

    # fallback (important)
    if re.search(r'\breplac(e|ed|ement)\b', text) and re.search(r'\b(pipe|piping)\b', text):
        my_set.add("Piping section replacement")

    if re.search(r'\breplac(e|ed|ement)\b', text) and re.search(r'\b(elbow|elbows)\b', text):
        my_set.add("Elbow replacement")

    if re.search(r'\b(extend|extends|extending|extended)\b', text, re.IGNORECASE) and re.search(r'\b(pipe|piping|pipes)\b', text, re.IGNORECASE):
        my_set.add("Pipe extension")
        
    return list(my_set)


def detect_pump_compressor_vessel_psv_scope(user_input) -> bool:#(problem_statement: str, proposed_solution: str) -> bool:
    #text = f"{problem_statement} {proposed_solution}".lower()
    text = user_input.lower()

    keywords = [
        "pump",
        "compressor",
        "vessel",
        "vessel nozzle",
        "nozzle",
        "psv",
        "pressure safety valve",
        "relief valve"
    ]

    return any(k in text for k in keywords)


def detect_new_piping_route(user_input) -> bool:#(problem_statement: str, proposed_solution: str) -> bool:
    #text = f"{problem_statement} {proposed_solution}".lower()
    text = user_input.lower()

    keywords = [
        "new piping route",
        "reroute",
        "re-route",
        "new route",
        "pipe support foundation",
        "support foundation",
        "excavation",
        "surveying work",
        "underground utilities",
        "unpaved areas",
        "install new support",
        "new support location",
        "new pipe rack",
        "new underground line",
        "new aboveground route"
    ]

    return any(k in text for k in keywords)


def detect_replace_existing_equipment_diff_weight(user_input) -> bool:#(problem_statement: str, proposed_solution: str) -> bool:
    #text = f"{problem_statement} {proposed_solution}".lower()
    text = user_input.lower()

    keywords = [
        "different weight",
        "new equipment indicated on drawing",
        "replacing existing equipment",
        "replace existing equipment",
        "equipment of different weight",
        "weight of the new equipment",
        "lifting plan",
        "center of gravity",
        "load change",
        "foundation load change"
    ]

    return any(k in text for k in keywords)


def parse_plain_input(user_input: str) -> dict:
    """
    Supports input like:

    Problem statement: Leak detected on ...
    Proposed solution: Replace ...
    """
    if not user_input or not isinstance(user_input, str):
        return {
            "problem_statement": "",
            "proposed_solution": ""
        }

    text = user_input.strip()

    problem_match = re.search(
        r'problem\s*statement\s*:\s*(.*?)(?=proposed\s*solution\s*:|$)',
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    solution_match = re.search(
        r'proposed\s*solution\s*:\s*(.*)',
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    problem_statement = problem_match.group(1).strip() if problem_match else ""
    proposed_solution = solution_match.group(1).strip() if solution_match else ""

    return {
        "problem_statement": problem_statement,
        "proposed_solution": proposed_solution
    }

@tool
def build_scope_json_from_input(user_input: str) -> dict:
    """
    Supports 2 input formats:

    1) JSON string:
       {"problem_statement": "...", "proposed_solution": "..."}

    2) Plain text string:
       Problem statement: ...
       Proposed solution: ...
    """

    data = None

    # First try JSON
    try:
        data = json.loads(user_input) if isinstance(user_input, str) else user_input
    except Exception:
        data = None

    # If not JSON, parse plain text
    if not isinstance(data, dict):
        data = parse_plain_input(user_input)

    if not isinstance(data, dict):
        return {
            "error": "Input must be either valid JSON string or plain text with 'Problem statement:' and 'Proposed solution:'."
        }

    problem_statement = (data.get("problem_statement", "") or "").strip()
    proposed_solution = (data.get("proposed_solution", "") or "").strip()

    combined_text = f"{problem_statement}\n{proposed_solution}"

    def detect_insulation_tool(user_input: str) -> dict:
        is_ins, code = detect_insulation(user_input)
        return is_ins

    def detect_heat_tracing_tool(user_input: str) -> Optional[List[str]]:
        return detect_heat_tracing(user_input)

    IE_DOC_PATTERN = re.compile(r'I\s*&\s*E\s*Job\s*Pack[\s:#-]*([A-Za-z0-9]+(?:-[A-Za-z0-9]+)+)', re.IGNORECASE)

    def extract_ie_doc_no(user_input: str):
        if not user_input:
            return False
        m = IE_DOC_PATTERN.search(user_input)
        return m.group(1).upper() if m else False

    def my_python_tool(line_class: str, user_input) -> dict[str, Any]:
        filters = []

        line_class = (line_class or "").strip()
        dia_inch = extract_dia_in(user_input)

        return dia_inch

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

    # Unicode vulgar fractions -> ASCII equivalents
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
        # collapse cases like "1 1/2" -> "1 1/2", and "1. 1/2" -> "1 1/2"
        s = re.sub(r'(\d)\.\s*(\d+/\d+)', r'\1 \2', s)
        s = re.sub(r'\s+', ' ', s)
        return s

    def extract_dia_in(text: str):
        text = str(text or "").lower()
        text = _normalize_fractions(text)
        # size token pattern:
        # 1 1/2
        # 1.1/2
        # 1/2
        # 10
        #size_pattern = r"(\d+\s+\d+/\d+|\d+\.\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)"
        size_pattern = r'(?:\d+\s+\d+/\d+|\d+\.\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)'

        patterns = [
            # 1) explicit diameter (unit optional here is OK — the word "diameter" is the anchor)
            rf'diameter\s*[:=]?\s*({size_pattern})\s*(?:inches\b|inch\b|in\b|")?',

            # 2) explicit pipe size
            rf'pipe\s*size\s*[:=]?\s*({size_pattern})\s*(?:inches\b|inch\b|in\b|")?',

            # 3) NPS
            rf'nps\s*[:=]?\s*({size_pattern})\s*(?:inches\b|inch\b|in\b|")?',

            # 4) spec format — INCH MARK NOW REQUIRED  (was "?  ->  now mandatory)
            rf'-({size_pattern})\s*(?:"|''|in\b)\s*-\s*(\d+[A-Za-z]+\d*[A-Za-z]*)(?=[\s\.,;:]|$)',

            # 5) generic standalone size WITH a unit (unchanged)
            rf'\b({size_pattern})\s*(?:"|inches\b|inch\b|in\b)',

            # 6) spec format with quoted size before code — INCH MARK NOW REQUIRED
            rf'-({size_pattern})\s*(?:"|in\b)\s*-\s*\d+[A-Za-z]+\d*'
    ]

        for pattern in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                value = parse_size_token(m.group(1))
                if value is not None:
                    return [value]

        return []

    #scope_type = detect_scope_type(problem_statement, proposed_solution)

    line_class_temp = extract_line_class(user_input)
    line_class = get_legacy_class_line(line_class_temp, user_input)

    scope_type = detect_scope_type(user_input)

    insulation = detect_insulation_tool(user_input)

    heat_tracing = detect_heat_tracing(user_input)

    hydrogen_bake_out = is_special_service(line_class)

    ie_doc_no = extract_ie_doc_no(user_input)

    dia_in = my_python_tool(line_class, user_input)

    placeholders_TP = extract_tp_placeholders(user_input)

    # spool_prefab
    if "Piping section replacement" in scope_type:
        spool_prefab = True
    else:
        spool_prefab = False

    # has_tie_ins
    try:
        has_tie_ins = len(placeholders_TP) > 0
    except TypeError:
        has_tie_ins = False

    # pump_compressor_vessel_psv_in_scope
    if detect_pump_compressor_vessel_psv_scope(user_input):#(problem_statement, proposed_solution):
        pump_compressor_vessel_psv_in_scope = True
    else:
        pump_compressor_vessel_psv_in_scope = False

    # new_piping_route
    if detect_new_piping_route(user_input):#(problem_statement, proposed_solution):
        new_piping_route = True
    else:
        new_piping_route = False

    # insufficient_vessel_internal_data
    if pump_compressor_vessel_psv_in_scope:
        insufficient_vessel_internal_data = True
    else:
        insufficient_vessel_internal_data = False

    # replace_existing_equipment_diff_weight
    if detect_replace_existing_equipment_diff_weight(user_input):#(problem_statement, proposed_solution):
        replace_existing_equipment_diff_weight = True
    else:
        replace_existing_equipment_diff_weight = False

    return {
        #"problem_statement": problem_statement,
        #"proposed_solution": proposed_solution,
        'line_class': line_class,
        "scope_type": scope_type,
        'insulation': insulation,
        'heat_tracing': heat_tracing,
        'hydrogen_bake_out': hydrogen_bake_out,
        'ie_doc_no': ie_doc_no,
        'dia_in': dia_in,
        'existing_spring_support_reuse': True,
        "placeholders_TP": placeholders_TP,
        "spool_prefab": spool_prefab,
        "has_tie_ins": has_tie_ins,
        "pump_compressor_vessel_psv_in_scope": pump_compressor_vessel_psv_in_scope,
        "new_piping_route": new_piping_route,
        "insufficient_vessel_internal_data": insufficient_vessel_internal_data,
        "replace_existing_equipment_diff_weight": replace_existing_equipment_diff_weight
    }