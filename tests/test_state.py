"""Unit tests for pf_jobpack.state — merge / validate / route / load."""

from pf_jobpack.state import (
    EMPTY_STATE,
    REQUIRED_FIELDS,
    load_state,
    merge_state,
    route_prev,
    validate_state,
)


class TestMergeState:
    def test_empty_new_values_never_overwrite(self):
        prev = {"line_class": "150A20"}
        merged = merge_state(prev, {"line_class": "", "scope_type": None})
        assert merged["line_class"] == "150A20"

    def test_lists_are_unioned_dedup(self):
        merged = merge_state({"dia_in": [2.0]}, {"dia_in": [2.0, 4.0]})
        assert merged["dia_in"] == [2.0, 4.0]

    def test_bool_is_monotonic_true_wins(self):
        assert merge_state({"spool_prefab": True}, {"spool_prefab": False})["spool_prefab"] is True
        assert merge_state({"spool_prefab": False}, {"spool_prefab": True})["spool_prefab"] is True

    def test_correctable_field_overwrites(self):
        merged = merge_state({"line_class": "150A20"}, {"line_class": "300C80"})
        assert merged["line_class"] == "300C80"

    def test_non_correctable_is_sticky(self):
        merged = merge_state({"insufficient_vessel_internal_data": "x"},
                             {"insufficient_vessel_internal_data": "y"})
        assert merged["insufficient_vessel_internal_data"] == "x"


class TestValidateState:
    def test_complete_when_all_present(self):
        state = {f: "v" for f in REQUIRED_FIELDS}
        result = validate_state(state)
        assert result["complete"] is True
        assert result["missing"] == []

    def test_missing_reported(self):
        state = {f: "v" for f in REQUIRED_FIELDS}
        state["line_class"] = None
        state["scope_type"] = "null"
        result = validate_state(state)
        assert result["complete"] is False
        assert set(result["missing"]) == {"line_class", "scope_type"}

    def test_accepts_json_string_with_fences(self):
        result = validate_state('```json\n{"line_class": "150A20"}\n```')
        assert result["state"]["line_class"] == "150A20"


class TestRoutePrev:
    def test_dict_input(self):
        out = route_prev({"line_class": "150A20"})
        assert out["kind"] == "json"
        assert out["as_dict"] == {"line_class": "150A20"}

    def test_json_string_input(self):
        out = route_prev('{"line_class": "150A20"}')
        assert out["kind"] == "json"
        assert out["as_dict"]["line_class"] == "150A20"

    def test_plain_string_input(self):
        out = route_prev("Which line class?")
        assert out["kind"] == "string"
        assert out["as_string"] == "Which line class?"


class TestLoadState:
    def test_empty_history_returns_empty_state(self):
        assert load_state([]) == EMPTY_STATE

    def test_returns_last_merge_state(self):
        history = [
            {"outputs": {"merge_state": {"line_class": "150A20"}}},
            {"outputs": {"merge_state": {"line_class": "300C80"}}},
        ]
        loaded = load_state(history)
        assert loaded["line_class"] == "300C80"
        # spring support is force-set to True on load.
        assert loaded["existing_spring_support_reuse"] is True
