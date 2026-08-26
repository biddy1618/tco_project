"""Unit tests for pf_jobpack.material.check_material_ss.

Cases are taken from the real ``nde.csv`` material vocabulary so this doubles
as documentation of how each family classifies.
"""

import pytest

from pf_jobpack.material import check_material_ss


def _doc(material_phrase, line_class="150X00"):
    content = f"Pipe line class {line_class}. Material {material_phrase}."
    return [{"text": content, "metadata": "100"}]


@pytest.mark.parametrize(
    "phrase,expected",
    [
        # --- Carbon steel families -> CS ---
        ("LTCS", "CS"),
        ("LTCS NACE", "CS"),
        ("CS BITUM COATED", "CS"),
        ("CS GALV BITUM COATED", "CS"),
        ("LTCS GALV", "CS"),
        ("LTCS NACE - API 5L X60 (SMLS)", "CS"),
        ("LTCS PTFE Lined", "CS"),
        ("PTFE lined LTCS", "CS"),
        ("CS+inclonel 625 CLAD (API 5LD)", "CS"),
        ("ASTM A105 CS", "CS"),
        ("LTCS - SMYS <= 42 ksi (290 Mpa)", "CS"),
        # --- Stainless -> SS ---
        ("316/L SS", "SS"),
        ("316 SS", "SS"),
        ("316/316L SS", "SS"),
        ("CrNi SS (ASTM A358)", "SS"),
        # --- Everything else -> Null ---
        ("Alloy 20", "Null"),
        ("Inconel 825", "Null"),
        ("Super Duplex UNS S32760", "Null"),
        ("Glass Reinforced Epoxy", "Null"),
        ("HDPE", "Null"),
        ("6% Moly (UNS31254)", "Null"),
        ("Monel 400", "Null"),
        ("1.25 Cr - 0.5 Mo", "Null"),
        ("API 5L X60", "Null"),
    ],
)
def test_classification(phrase, expected):
    assert check_material_ss(_doc(phrase)) == expected


class TestEdgeCases:
    def test_empty_input(self):
        assert check_material_ss([]) == "No"
        assert check_material_ss(None) == "No"

    def test_no_material_phrase(self):
        assert check_material_ss([{"text": "Pipe line class 150A20."}]) == "No"

    def test_reads_nested_content(self):
        item = [{"metadata": {"content": "Material 316/L SS."}}]
        assert check_material_ss(item) == "SS"
