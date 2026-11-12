"""Worked prose examples must agree with the bundled deterministic source grammar."""
import os
from pathlib import Path
import sys

SKILL = Path(os.environ.get("SKO_TEST_SKILL_ROOT", Path(__file__).parents[1]))
sys.path.insert(0, str(SKILL / "scripts"))
import _ldo_v3 as lint


def test_topical_worked_facts_match_the_source_grammar(tmp_path):
    text = (SKILL / "references/facts-to-llms-howto.md").read_text()
    excerpt = text.split("Facts excerpt:", 1)[1].split("```", 2)[1]
    rows = [line for line in excerpt.splitlines() if line.startswith("- [")]
    assert len(rows) == 2
    findings = lint.pass_facts("# Fixture facts\n\n" + "\n".join(rows), tmp_path / "facts.txt", None)
    assert not [f for f in findings if f["severity"] == "high"], findings


def test_headingless_source_and_broken_fragment_are_distinct():
    headings = {"/fixture/plain.md": set()}
    assert not lint._anchor_unresolved(headings, "/fixture/plain.md")
    assert lint._anchor_unresolved(headings, "/fixture/plain.md#top")
