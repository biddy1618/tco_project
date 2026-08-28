"""Tracker test IDs resolve to deducted prompts; TC-001 is first-turn complete."""

from maf.cases import deducted_prompt, load_cases, resolve_question
from pf_jobpack.extraction import build_scope_json_from_input
from pf_jobpack.state import load_state, merge_state, validate_state


def test_load_all_tracker_ids():
    cases = load_cases()
    assert "TC-001" in cases
    assert "TC-002" in cases
    assert len(cases) == 36


def test_resolve_test_id():
    prompt = resolve_question("TC-002")
    assert prompt.startswith("120-SL04-24-150H03")
    assert "TA-2024" in prompt


def test_resolve_free_text_unchanged():
    text = "replace the leaking valve"
    assert resolve_question(text) == text


def test_unknown_test_id():
    try:
        deducted_prompt("TC-099")
    except KeyError as exc:
        assert "TC-099" in str(exc)
        return
    raise AssertionError("expected KeyError")


def test_literal_tc_002_is_not_the_case():
    """Passing the ID as repair text (old CLI) extracts almost nothing."""
    state = build_scope_json_from_input("TC-002")
    assert state.get("line_class") in ("", None)
    assert state.get("dia_in") == []


def test_tc001_first_turn_is_complete():
    prompt = deducted_prompt("TC-001")
    extracted = build_scope_json_from_input(prompt)
    merged = merge_state(load_state([]), extracted)
    result = validate_state(merged)
    assert extracted["dia_in"] == [0.5]
    assert merged["placeholders_TP"] == ["TP-001", "TP-002"]
    assert result["complete"] is True, result["missing"]
    assert result["missing"] == []


def test_tc002_tbd_tieins_do_not_block():
    """[tie-in IDs TBD] is not a missing field — ID003 still emitted a pack."""
    prompt = deducted_prompt("TC-002")
    merged = merge_state(load_state([]), build_scope_json_from_input(prompt))
    result = validate_state(merged)
    assert merged["placeholders_TP"] == []
    assert "placeholders_TP" not in result["missing"]
    assert result["complete"] is True, result["missing"]
