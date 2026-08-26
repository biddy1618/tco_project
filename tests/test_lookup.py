"""Unit tests for pf_jobpack.lookup — the shape-tolerant result parsing that
underpins the material + NDE fixes.

These pin the behaviour that broke against the live ``ndeee`` index: the rich
``content`` sentence must be found across several serializations, and PMI must
be read as a number even when it arrives as the string ``"100"``.
"""

from pf_jobpack.lookup import get_pmi_percent, get_result_content, pmi_requires_pmi

CONTENT = "Pipe line class 150A20. Design code ASME B31.3. Material Alloy 20. PMI 100.0."


class TestGetResultContent:
    def test_text_key(self):
        assert get_result_content({"text": CONTENT}) == CONTENT

    def test_page_content_key(self):
        assert get_result_content({"page_content": CONTENT}) == CONTENT

    def test_content_key(self):
        assert get_result_content({"content": CONTENT}) == CONTENT

    def test_nested_metadata_content(self):
        assert get_result_content({"metadata": {"content": CONTENT}}) == CONTENT

    def test_nested_additional_fields_content(self):
        assert get_result_content({"additional_fields": {"content": CONTENT}}) == CONTENT

    def test_plain_string(self):
        assert get_result_content(CONTENT) == CONTENT

    def test_empty_and_none(self):
        assert get_result_content(None) == ""
        assert get_result_content({}) == ""
        assert get_result_content({"text": "  "}) == ""


class TestGetPmiPercent:
    def test_string_metadata_100(self):
        # This is the exact live shape that used to break (Edm.String "100").
        assert get_pmi_percent({"text": CONTENT, "metadata": "100"}) == 100.0

    def test_int_metadata(self):
        assert get_pmi_percent({"text": CONTENT, "metadata": 100}) == 100.0

    def test_float_metadata(self):
        assert get_pmi_percent({"text": CONTENT, "metadata": 100.0}) == 100.0

    def test_pmi_percent_nested(self):
        assert get_pmi_percent({"metadata": {"pmi_percent": "100"}}) == 100.0

    def test_parsed_from_content_sentence(self):
        # No metadata at all -> fall back to "PMI 100.0" in the text.
        assert get_pmi_percent({"text": CONTENT}) == 100.0

    def test_missing_pmi_returns_none(self):
        no_pmi = "Pipe line class 150H0G. Material LTCS."
        assert get_pmi_percent({"text": no_pmi}) is None
        assert get_pmi_percent({"text": no_pmi, "metadata": None}) is None

    def test_bool_metadata_is_not_pmi(self):
        assert get_pmi_percent({"text": "Material LTCS.", "metadata": True}) is None


class TestPmiRequiresPmi:
    def test_true_for_100(self):
        assert pmi_requires_pmi({"text": CONTENT, "metadata": "100"}) is True

    def test_false_when_absent(self):
        assert pmi_requires_pmi({"text": "Material LTCS."}) is False
