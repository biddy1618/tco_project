"""Scope detection and input parsing helpers for the job-pack flow."""

from __future__ import annotations

import json
import re


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
        cleaned = cleaned.upper()

        if cleaned not in seen:
            seen.add(cleaned)
            unique.append(cleaned)
    return unique


def detect_scope_type(user_input) -> list:
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

    if re.search(r'\breplac(e|ed|ement)\b', text) and re.search(r'\b(pipe|piping)\b', text):
        detected.add("Piping section replacement")

    if re.search(r'\breplac(e|ed|ement)\b', text) and re.search(r'\b(elbow|elbows)\b', text):
        detected.add("Elbow replacement")

    if re.search(r'\b(extend|extends|extending|extended)\b', text, re.IGNORECASE) and re.search(r'\b(pipe|piping|pipes)\b', text, re.IGNORECASE):
        detected.add("Pipe extension")

    return list(detected)


def detect_pump_compressor_vessel_psv_scope(user_input) -> bool:
    text = user_input.lower()

    keywords = [
        "pump",
        "compressor",
        "vessel",
        "vessel nozzle",
        "nozzle",
        "psv",
        "pressure safety valve",
        "relief valve",
    ]

    return any(keyword in text for keyword in keywords)


def detect_new_piping_route(user_input) -> bool:
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
        "new aboveground route",
    ]

    return any(keyword in text for keyword in keywords)


def detect_replace_existing_equipment_diff_weight(user_input) -> bool:
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
        "foundation load change",
    ]

    return any(keyword in text for keyword in keywords)


def parse_plain_input(user_input: str) -> dict:
    if not user_input or not isinstance(user_input, str):
        return {"problem_statement": "", "proposed_solution": ""}

    text = user_input.strip()

    problem_match = re.search(
        r'problem\s*statement\s*:\s*(.*?)(?=proposed\s*solution\s*:|$)',
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    solution_match = re.search(
        r'proposed\s*solution\s*:\s*(.*)',
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    problem_statement = problem_match.group(1).strip() if problem_match else ""
    proposed_solution = solution_match.group(1).strip() if solution_match else ""

    return {"problem_statement": problem_statement, "proposed_solution": proposed_solution}


def build_scope_json_from_input(user_input: str) -> dict:
    data = None

    try:
        data = json.loads(user_input) if isinstance(user_input, str) else user_input
    except Exception:
        data = None

    if not isinstance(data, dict):
        data = parse_plain_input(user_input)

    if not isinstance(data, dict):
        return {
            "error": "Input must be either valid JSON string or plain text with 'Problem statement:' and 'Proposed solution:'.",
        }

    problem_statement = (data.get("problem_statement", "") or "").strip()
    proposed_solution = (data.get("proposed_solution", "") or "").strip()

    _combined_text = f"{problem_statement}\n{proposed_solution}"

    scope_type = detect_scope_type(user_input)
    placeholders_TP = extract_tp_placeholders(user_input)

    spool_prefab = "Piping section replacement" in scope_type
    has_tie_ins = len(placeholders_TP) > 0
    pump_compressor_vessel_psv_in_scope = detect_pump_compressor_vessel_psv_scope(user_input)
    new_piping_route = detect_new_piping_route(user_input)
    insufficient_vessel_internal_data = pump_compressor_vessel_psv_in_scope
    replace_existing_equipment_diff_weight = detect_replace_existing_equipment_diff_weight(user_input)

    return {
        "problem_statement": problem_statement,
        "proposed_solution": proposed_solution,
        "scope_type": scope_type,
        "placeholders_TP": placeholders_TP,
        "spool_prefab": spool_prefab,
        "has_tie_ins": has_tie_ins,
        "pump_compressor_vessel_psv_in_scope": pump_compressor_vessel_psv_in_scope,
        "new_piping_route": new_piping_route,
        "insufficient_vessel_internal_data": insufficient_vessel_internal_data,
        "replace_existing_equipment_diff_weight": replace_existing_equipment_diff_weight,
    }