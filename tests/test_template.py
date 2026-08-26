"""Integration-ish tests for pf_jobpack.template.build_job_pack.

These focus on the scope_type list fix and the material / NDE / PWHT wiring,
which are the behaviours a smaller model is most likely to regress.
"""

from pf_jobpack.template import build_job_pack


def make_facts(**overrides):
    facts = {
        "line_class": "150A20",
        "scope_type": [],
        "insulation": None,
        "heat_tracing": None,
        "hydrogen_bake_out": False,
        "ie_doc_no": False,
        "dia_in": [4.0],
        "existing_spring_support_reuse": True,
        "placeholders_TP": [],
        "spool_prefab": False,
        "has_tie_ins": False,
        "pump_compressor_vessel_psv_in_scope": False,
        "new_piping_route": False,
        "insufficient_vessel_internal_data": False,
        "replace_existing_equipment_diff_weight": False,
    }
    facts.update(overrides)
    return facts


def build(facts, nde_result="No", wps_result="No", material="Null"):
    out = build_job_pack(facts, nde_result, wps_result, material)
    assert isinstance(out, dict), out
    return out["final_text"]


class TestScopeTypeListHandling:
    def test_valve_only_skips_shop_work(self):
        # Regression: scope_type is a *list*; a pure valve replacement must
        # skip the SHOP WORK block. (Old code compared list == str -> always
        # ran the block.)
        text = build(make_facts(scope_type=["Valve replacement"]))
        assert "SHOP WORK:" not in text

    def test_valve_as_string_also_skips_shop_work(self):
        text = build(make_facts(scope_type="Valve replacement"))
        assert "SHOP WORK:" not in text

    def test_valve_plus_piping_runs_shop_work(self):
        text = build(make_facts(scope_type=["Valve replacement", "Piping section replacement"]))
        assert "SHOP WORK:" in text

    def test_piping_section_runs_shop_work(self):
        text = build(make_facts(scope_type=["Piping section replacement"], spool_prefab=True))
        assert "SHOP WORK:" in text
        assert "Prefabricate pipe spools" in text


class TestMaterialWiring:
    def test_cs_adds_coating_note(self):
        text = build(make_facts(scope_type=["Piping section replacement"], spool_prefab=True),
                     material="CS")
        assert "Abrasive blast and coat" in text

    def test_ss_adds_chloride_note(self):
        text = build(
            make_facts(scope_type=["Piping section replacement"], spool_prefab=True),
            wps_result="No",
            material="SS",
        )
        assert "chloride" in text.lower()


class TestNdeWiring:
    def test_nde_yes_adds_pmi_lines(self):
        text = build(make_facts(scope_type=["Piping section replacement"], spool_prefab=True),
                     nde_result="Yes")
        assert "Positive Material Identification" in text


class TestPwhtWiring:
    def test_wps_no_emits_field_weld_nde(self):
        # With a tie-in path ('52a') and wps 'No', line 57a (field-weld NDE)
        # must be emitted. This is what the blank-PWHT -> "No" fix protects.
        facts = make_facts(scope_type=["Piping section replacement"], has_tie_ins=True,
                           placeholders_TP=["TP-1001"], spool_prefab=True)
        text = build(facts, wps_result="No")
        assert "Perform NDE of field welds" in text

    def test_wps_yes_emits_pwht_lines(self):
        facts = make_facts(scope_type=["Piping section replacement"], has_tie_ins=True,
                           placeholders_TP=["TP-1001"], spool_prefab=True)
        text = build(facts, wps_result="Yes")
        assert "Perform PWHT" in text


class TestPassthrough:
    def test_non_json_string_facts_returned_as_is(self):
        assert build_job_pack("Which line class?", "No", "No", "Null") == "Which line class?"

    def test_long_wps_message_surfaces(self):
        msg = "Please recheck your diameter the mismatch might come from the range value listed"
        facts = make_facts(scope_type=["Piping section replacement"])
        assert build_job_pack(facts, "No", msg, "Null") == msg
