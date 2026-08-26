"""Material classification (CS / SS / Null) from the NDE lookup.

Port of the original ``material.py`` node with two fixes confirmed against the
live ``ndeee`` index (2026-08-25):

* The material text lives inside the index ``content`` sentence
  (e.g. ``"... Material Alloy 20. PMI 100.0."``); the dedicated ``material``
  field is ``retrievable=false``. The flow's ``nde`` node therefore maps
  ``content -> content`` so this sentence is available, and we read it via the
  shared, shape-tolerant :func:`pf_jobpack.lookup.get_result_content` helper
  (the original only handled ``metadata`` being a dict/int, which the live
  ``pmi_percent`` string broke).
* The CS check was a strict ``fullmatch`` on ``CS|LTCS|LTCS NACE``, so real
  values like ``CS BITUM COATED`` / ``LTCS GALV`` / ``LTCS NACE - API 5L X60``
  fell through to ``Null``. It is now an anchored prefix match so any
  carbon-steel variant classifies as ``CS`` (behavioural change — see
  docs/flow-structure.md §6).
"""

from __future__ import annotations

import re
from typing import Any, List

from pf_jobpack.lookup import get_result_content

# Carbon-steel families: match a standalone CS / LTCS token anywhere in the
# material text so coated / galvanized / NACE / API-grade / lined variants
# ("CS BITUM COATED", "LTCS GALV", "LTCS NACE - API 5L X60 (SMLS)",
# "PTFE lined LTCS", "ASTM A105 CS") are still classified as CS.
_CS_WORD = re.compile(r"\b(LTCS|CS)\b", re.IGNORECASE)
_SS_WORD = re.compile(r"\bSS\b", re.IGNORECASE)
_MATERIAL_RE = re.compile(r"Material\s+(.+?)(?:\.|$)", re.IGNORECASE)


def check_material_ss(search_output: List[dict]) -> str:
    if not search_output:
        return "No"

    content = get_result_content(search_output[0])
    if not content.strip():
        return "No"

    match = _MATERIAL_RE.search(content)
    if not match:
        return "No"

    material_text = match.group(1).strip()

    # SS is checked first: "316/L SS", "CrNi SS" etc. never start with CS/LTCS,
    # so ordering here only matters for safety.
    if _SS_WORD.search(material_text):
        return "SS"
    if _CS_WORD.search(material_text):
        return "CS"
    return "Null"
