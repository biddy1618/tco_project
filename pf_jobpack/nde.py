"""NDE (non-destructive examination) / PMI lookup evaluation.

Port of the original ``nde_py.py`` node, with two correctness fixes confirmed
against the live ``ndeee`` index (2026-08-25):

* The original compared ``metadata == 100`` (int). The index actually returns
  ``pmi_percent`` as the **string** ``"100"``, so that check was always False
  and PMI never triggered. We now parse the value numerically via
  :func:`pf_jobpack.lookup.get_pmi_percent`.
* The line-class presence check and content access are made robust to the
  different result shapes ``common_index_lookup`` can emit (see
  :mod:`pf_jobpack.lookup`).

Two defensive guards from the previous port are retained (empty result and
missing content return ``None`` instead of raising).
"""

from __future__ import annotations

from typing import List, Optional

from pf_jobpack.lookup import get_pmi_percent, get_result_content


def check_nde_search(input1: List[dict], line_class: str) -> Optional[str]:
    if not input1:
        return None

    content = get_result_content(input1[0])
    if not content:
        return None

    # The retrieved document must actually correspond to the queried line class.
    if line_class and line_class.upper() not in content.upper():
        return None

    pmi = get_pmi_percent(input1[0])
    if pmi is None:
        return "No"
    return "Yes" if pmi >= 100.0 else "No"
