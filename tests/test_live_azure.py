"""Opt-in LIVE checks against the real Azure AI Search service.

These validate that the node logic produces the right answers on *real*
documents (not just synthetic fixtures) — the highest-value guardrail when a
smaller model is editing the code.

They are skipped unless an API key is provided. To run:

    export AZURE_SEARCH_API_KEY='<query or admin key>'
    # optional (defaults shown):
    export AZURE_SEARCH_ENDPOINT='https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net'
    export AZURE_SEARCH_API_VERSION='2023-11-01'
    pytest -m live -v

The key is read from the environment only — never commit it.
"""

import os

import pytest
import requests

from pf_jobpack.material import check_material_ss
from pf_jobpack.nde import check_nde_search
from pf_jobpack.pwht import check_pwht_flag

ENDPOINT = os.environ.get(
    "AZURE_SEARCH_ENDPOINT",
    "https://pf-t332-cog-srch-test-euw1-cvx.search.windows.net",
).rstrip("/")
API_KEY = os.environ.get("AZURE_SEARCH_API_KEY")
API_VERSION = os.environ.get("AZURE_SEARCH_API_VERSION", "2023-11-01")

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not API_KEY, reason="set AZURE_SEARCH_API_KEY to run live tests"),
]


def _search(index, body):
    url = f"{ENDPOINT}/indexes/{index}/docs/search?api-version={API_VERSION}"
    r = requests.post(
        url,
        headers={"Content-Type": "application/json", "api-key": API_KEY},
        json=body,
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("value", [])


def _fetch_ndeee_doc(line_class):
    docs = _search(
        "ndeee",
        {
            "search": line_class,
            "queryType": "simple",
            "searchFields": "line_class",
            "select": "line_class,content,pmi_percent",
            "top": 5,
        },
    )
    for d in docs:
        if str(d.get("line_class", "")).upper() == line_class.upper():
            return d
    return docs[0] if docs else None


def _as_lookup_item(doc):
    """Reproduce the shape the flow's `nde` node emits after its field_mapping
    (content -> content, metadata -> pmi_percent)."""
    return {"text": doc.get("content", ""), "metadata": doc.get("pmi_percent")}


class TestNdeeeLive:
    @pytest.mark.parametrize(
        "line_class,expected_material,expected_nde",
        [
            ("150N01", "SS", "Yes"),   # 316/L SS, PMI 100
            ("150H0G", "CS", "No"),    # LTCS, no PMI
            ("150A20", "Null", "Yes"), # Alloy 20, PMI 100
        ],
    )
    def test_material_and_nde(self, line_class, expected_material, expected_nde):
        doc = _fetch_ndeee_doc(line_class)
        assert doc is not None, f"no ndeee doc for {line_class}"
        item = [_as_lookup_item(doc)]
        assert check_material_ss(item) == expected_material
        assert check_nde_search(item, line_class) == expected_nde


class TestWpsLive:
    def test_pwht_for_known_class(self):
        docs = _search(
            "wps-diain",
            {
                "search": "150A20",
                "queryType": "simple",
                "searchFields": "line_class",
                "select": "line_class,pwht,dia_in1,dia_in2",
                "top": 3,
            },
        )
        assert docs, "no wps-diain doc for 150A20"
        # Reproduce the wps_api output shape and evaluate.
        result = check_pwht_flag({"value": docs}, "150A20")
        assert result in ("Yes", "No")
        # From the confirmed sample, 150A20 has pwht "N".
        assert result == "No"
