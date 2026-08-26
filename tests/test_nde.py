"""Unit tests for pf_jobpack.nde.check_nde_search."""

from pf_jobpack.nde import check_nde_search

PMI_CONTENT = "Pipe line class 150A20. Design code ASME B31.3. Material Alloy 20. PMI 100.0."
NO_PMI_CONTENT = "Pipe line class 150H0G. Design code ASME B31.3. Material LTCS."


def _result(content, metadata=None):
    item = {"text": content}
    if metadata is not None:
        item["metadata"] = metadata
    return [item]


class TestCheckNdeSearch:
    def test_pmi_100_string_metadata_yields_yes(self):
        # Regression: the live index returns pmi as the string "100".
        assert check_nde_search(_result(PMI_CONTENT, "100"), "150A20") == "Yes"

    def test_pmi_100_parsed_from_content_when_no_metadata(self):
        assert check_nde_search(_result(PMI_CONTENT), "150A20") == "Yes"

    def test_no_pmi_yields_no(self):
        assert check_nde_search(_result(NO_PMI_CONTENT), "150H0G") == "No"

    def test_empty_input_returns_none(self):
        assert check_nde_search([], "150A20") is None
        assert check_nde_search(None, "150A20") is None

    def test_line_class_mismatch_returns_none(self):
        # Retrieved doc is for a different class than requested.
        assert check_nde_search(_result(PMI_CONTENT, "100"), "999Z99") is None

    def test_line_class_case_insensitive(self):
        assert check_nde_search(_result(PMI_CONTENT, "100"), "150a20") == "Yes"

    def test_missing_content_returns_none(self):
        assert check_nde_search([{"metadata": "100"}], "150A20") is None
