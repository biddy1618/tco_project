"""Unit tests for pf_jobpack.search.build_wps_query (query building only;
the HTTP call is covered by the opt-in live test)."""

from pf_jobpack.search import build_wps_query


class TestBuildWpsQuery:
    def test_string_passthrough(self):
        # A pending follow-up question must pass straight through untouched.
        assert build_wps_query(as_string="What diameter?", as_dict={}) == "What diameter?"

    def test_line_class_and_diameter_filter(self):
        body = build_wps_query(as_string="", as_dict={"line_class": "150A20", "dia_in": [4.0]})
        assert body["search"] == "150A20"
        assert body["filter"] == "dia_in1 le 4.0 and dia_in2 ge 4.0"
        assert body["semanticConfiguration"] == "wps-diain-semantic-configuration"
        assert body["top"] == 6

    def test_uses_last_diameter(self):
        body = build_wps_query(as_string="", as_dict={"line_class": "150A20", "dia_in": [2.0, 8.0]})
        assert body["filter"] == "dia_in1 le 8.0 and dia_in2 ge 8.0"

    def test_no_line_class_defaults_to_wildcard(self):
        body = build_wps_query(as_string="", as_dict={})
        assert body["search"] == "*"
        assert body["filter"] == ""

    def test_no_diameter_means_no_filter(self):
        body = build_wps_query(as_string="", as_dict={"line_class": "150A20"})
        assert body["filter"] == ""
