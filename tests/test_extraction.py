"""Unit tests for pf_jobpack.extraction."""

from pf_jobpack.extraction import (
    build_scope_json_from_input,
    detect_insulation,
    detect_scope_type,
    extract_dia_in,
    extract_ie_doc_no,
    extract_line_class,
    is_special_service,
)
from pf_jobpack.state import REQUIRED_FIELDS


class TestLineClass:
    def test_explicit_line_class(self):
        assert extract_line_class("line class 300C80") == "300C80"

    def test_full_spec_token(self):
        assert extract_line_class('62-0300-PHC-1001-10"-300C80-HCW5') == "300C80"

    def test_none_found(self):
        assert extract_line_class("just some words") == ""


class TestScopeType:
    def test_returns_list(self):
        assert isinstance(detect_scope_type("replace the valve"), list)

    def test_valve(self):
        assert "Valve replacement" in detect_scope_type("please replace the valve")

    def test_flange(self):
        assert "Flange replacement" in detect_scope_type("flange replacement required")

    def test_piping_section(self):
        assert "Piping section replacement" in detect_scope_type("replace the leaking pipe section")

    def test_elbow(self):
        assert "Elbow replacement" in detect_scope_type("replace the elbow")

    def test_multiple_scopes_can_coexist(self):
        scopes = detect_scope_type("replace the valve and replace the pipe")
        assert "Valve replacement" in scopes
        assert "Piping section replacement" in scopes


class TestInsulation:
    def test_ni_code_is_uninsulated(self):
        assert detect_insulation('10"-300C80-NI') == (False, "NI")

    def test_hcw_code_is_insulated(self):
        insulated, code = detect_insulation('10"-300C80-HCW5')
        assert insulated is True
        assert code == "HCW5"

    def test_nothing_detected(self):
        assert detect_insulation("replace the pipe section please") == (None, None)


class TestDiameter:
    def test_plain_inches(self):
        assert extract_dia_in('diameter 4"') == [4.0]

    def test_fraction(self):
        assert extract_dia_in('pipe size 3/4"') == [0.75]

    def test_none(self):
        assert extract_dia_in("no size given") == []


class TestIeDocNo:
    def test_extracts_doc_no(self):
        assert extract_ie_doc_no("see I&E Job Pack AB-1234-CD") == "AB-1234-CD"

    def test_absent_returns_false(self):
        assert extract_ie_doc_no("no doc here") is False


class TestSpecialService:
    def test_k_series(self):
        assert is_special_service("150K01") is True

    def test_c80(self):
        assert is_special_service("150C80") is True

    def test_regular(self):
        assert is_special_service("150H0G") is False


class TestBuildScopeJson:
    def test_returns_all_required_fields(self):
        state = build_scope_json_from_input(
            'Problem statement: leak. Proposed solution: replace the pipe 10"-300C80-HCW5'
        )
        for field in REQUIRED_FIELDS:
            assert field in state, f"missing field: {field}"

    def test_hydrogen_bake_out_follows_special_service(self):
        state = build_scope_json_from_input(
            "Problem statement: x. Proposed solution: replace pipe line class 150K01"
        )
        assert state["hydrogen_bake_out"] is True
