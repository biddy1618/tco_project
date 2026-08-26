"""Helpers for reading Azure AI Search / ``common_index_lookup`` results.

The ``ndeee`` index lookup is consumed by two nodes (``nde_py`` and
``material``) that historically made brittle assumptions about the exact shape
of each result item. Confirmed against the live index (2026-08-25):

* ``pmi_percent`` comes back as the **string** ``"100"`` (``Edm.String``), not
  an int/float. The ``content`` field is a full sentence such as
  ``"... Material Alloy 20. PMI 100.0."``.
* Depending on the mlindex ``field_mapping`` and tool version, a single result
  item may expose its text under ``text`` / ``page_content`` / ``content`` and
  its metadata under ``metadata`` (which may itself be a scalar, a dict, or be
  duplicated under ``additional_fields``).

These helpers normalise all of those shapes so the callers can stay simple and
so behaviour no longer depends on one exact serialization.
"""

from __future__ import annotations

import re
from typing import Any, Optional

_PMI_IN_TEXT = re.compile(r"PMI\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)


def get_result_content(item: Any) -> str:
    """Return the best available free-text content for a lookup result item.

    Looks (in order) at the common keys used by ``common_index_lookup`` and the
    raw Azure Search REST shape, including nested ``metadata`` /
    ``additional_fields`` dicts.
    """
    if item is None:
        return ""
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return str(item)

    # Direct text-bearing keys, most specific first.
    for key in ("text", "page_content", "content"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value

    # Nested containers.
    for container_key in ("metadata", "additional_fields", "original_entity"):
        container = item.get(container_key)
        if isinstance(container, dict):
            for key in ("content", "text", "page_content"):
                value = container.get(key)
                if isinstance(value, str) and value.strip():
                    return value

    return ""


def _coerce_pmi(value: Any) -> Optional[float]:
    """Coerce a raw pmi value (int/float/str) to a float, or return None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        m = re.search(r"[0-9]+(?:\.[0-9]+)?", value)
        if m:
            try:
                return float(m.group(0))
            except ValueError:
                return None
    return None


def get_pmi_percent(item: Any) -> Optional[float]:
    """Return the PMI percentage for a lookup result as a float, or None.

    Tries the mapped ``metadata`` field first (which the flow maps to
    ``pmi_percent``), then any nested ``pmi_percent`` key, then finally parses
    ``"PMI 100.0"`` out of the free-text content.
    """
    if not isinstance(item, dict):
        return None

    # 1) The flow maps metadata -> pmi_percent, so metadata may itself be the
    #    scalar "100" (string) / 100 (number).
    pmi = _coerce_pmi(item.get("metadata"))
    if pmi is not None:
        return pmi

    # 2) Explicit pmi_percent anywhere obvious.
    for container_key in ("metadata", "additional_fields", "original_entity"):
        container = item.get(container_key)
        if isinstance(container, dict):
            pmi = _coerce_pmi(container.get("pmi_percent"))
            if pmi is not None:
                return pmi
    pmi = _coerce_pmi(item.get("pmi_percent"))
    if pmi is not None:
        return pmi

    # 3) Fall back to the "PMI 100.0" phrase in the content sentence.
    content = get_result_content(item)
    m = _PMI_IN_TEXT.search(content)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None

    return None


def pmi_requires_pmi(item: Any) -> bool:
    """True if the result indicates 100% PMI (i.e. PMI is required)."""
    pmi = get_pmi_percent(item)
    return pmi is not None and pmi >= 100.0
