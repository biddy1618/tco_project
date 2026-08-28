"""Unit tests for pf_jobpack.pwht.check_pwht_flag."""

from pf_jobpack.pwht import check_pwht_flag


def _acs(line_class, pwht):
    return {"value": [{"line_class": line_class, "pwht": pwht}]}


class TestPwht:
    def test_yes(self):
        assert check_pwht_flag(_acs("150K01", "Y"), "150K01") == "Yes"

    def test_no(self):
        assert check_pwht_flag(_acs("150A20", "N"), "150A20") == "No"

    def test_n_see_note_starts_with_n_is_no(self):
        # Live data has 17 rows literally "N see Note (7)".
        assert check_pwht_flag(_acs("150X", "N see Note (7)"), "150X") == "No"

    def test_blank_defaults_to_no(self):
        # Regression: blank used to return None, which dropped the field-weld
        # NDE (line 57a) from the template. Now defaults to "No".
        assert check_pwht_flag(_acs("150X", ""), "150X") == "No"
        assert check_pwht_flag(_acs("150X", None), "150X") == "No"

    def test_string_passthrough(self):
        assert check_pwht_flag("just a follow-up question", "150A20") == "just a follow-up question"

    def test_no_line_class_skips(self):
        assert check_pwht_flag(_acs("150A20", "Y"), "") is None

    def test_line_class_mismatch_returns_message(self):
        out = check_pwht_flag(_acs("999ZZ", "Y"), "150A20")
        assert isinstance(out, str) and "recheck" in out.lower()

    def test_empty_value_returns_message(self):
        out = check_pwht_flag({"value": []}, "150A20")
        assert isinstance(out, str) and "recheck" in out.lower()

    def test_space_in_paren_suffix_still_matches(self):
        # Extractor emits 300H21(A); index rows are 300H21 (A).
        assert check_pwht_flag(_acs("300H21 (A)", "N"), "300H21(A)") == "No"

    def test_skips_neighbor_class_ranked_first(self):
        # TC-027: semantic search returned 2 hits; value[0] was not 300H21(A).
        result = {
            "value": [
                {"line_class": "300H25 (A)", "pwht": "Y"},
                {"line_class": "300H21 (A)", "pwht": "N"},
            ]
        }
        assert check_pwht_flag(result, "300H21(A)") == "No"
