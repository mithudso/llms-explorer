"""Frozen plans must retain low scores, scope reviews and exact parent links."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("mongo_plan", Path(__file__).parents[1] / "scripts/plan_mongodb_research.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def inventory():
    rows = [{"id": str(i), "concept": f"Concept {i}", "rank": i + 1, "cvs": score,
             "decision": "RESEARCH", "parents": [f"Parent {i}"], "score": {"axes": {"nov": nov, "via": 4}},
             "coverage_category": coverage} for i, (score, nov, coverage) in enumerate([
                 (4.5, 4, "frontier"), (2.0, 3, "refresh-review"), (1.0, 0, "frontier"), (None, 3, "covered")])]
    return {"rows": rows, "gaps": ["0", "1", "2"], "cohorts": [
        {"id": "group", "row_ids": ["0", "1", "2", "3"], "source_family": "drivers",
         "source_affinity": "pool", "likely_source_materials": [], "source_strategy": "shared primary pages"}]}


def test_low_scores_and_reviews_are_accounted_for_without_blocking_runnable_members():
    plan = module.make_plan(inventory(), created="2026-10-22")
    assert len(plan["rows"]) == len(plan["handoff_assignments"]) == 4
    assert [c["status"] for c in plan["cohorts"]] == ["pending", "needs-review", "skipped"]
    run = plan["cohorts"][0]
    assert run["concepts"] == ["Concept 0", "Concept 1"]
    assert run["parents"] == {"Concept 0": "Parent 0", "Concept 1": "Parent 1"}
    assert plan["rows"][1]["mode"] == "revisit"
    assert plan == module.make_plan(inventory(), created="2026-10-22")


def test_unscored_gap_cannot_be_frozen():
    value = inventory()
    value["rows"][0]["cvs"] = None
    with pytest.raises(ValueError, match="CVS"):
        module.make_plan(value)


def test_legacy_case_preservation_keeps_canonical_provenance_without_alias_substitution():
    value = inventory()
    plan = module.make_plan(value, execution_labels={"0": "concept 0"})
    assert plan["rows"][0]["concept"] == "concept 0"
    assert plan["rows"][0]["canonical_concept"] == "Concept 0"
    assert "concept 0" in plan["handoff_assignments"]
    with pytest.raises(ValueError, match="variants"):
        module.make_plan(value, execution_labels={"0": "Different concept"})


@pytest.mark.parametrize("mutation", ["duplicate", "missing"])
def test_every_identity_has_exactly_one_assignment(mutation):
    value = inventory()
    if mutation == "duplicate":
        value["cohorts"][0]["row_ids"].append("0")
    else:
        value["cohorts"][0]["row_ids"].pop()
    with pytest.raises(ValueError, match="assignment"):
        module.make_plan(value)
