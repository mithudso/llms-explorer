"""CVS scoring preserves inventory identity and rejects unusable model output."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mongodb_score", ROOT / "scripts/score_mongodb_queue.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)
WEIGHTS = {"rel": .25, "use": .25, "nov": .2, "int": .15, "via": .15}


def test_scoring_keeps_hard_gated_rows_and_marks_refresh_separately():
    candidates = [{"id": "a", "concept": "A", "coverage_category": "frontier"},
                  {"id": "b", "concept": "B", "coverage_category": "refresh-review"}]
    rows = [{"id": value, "rel": 5, "use": 4, "nov": 3, "int": 2, "via": via,
             "rationale": "A specific operational research gap."} for value, via in [("a", 1), ("b", 5)]]
    result = score.validate({"rows": rows}, candidates, WEIGHTS)
    assert [row["decision"] for row in result] == ["SKIP", "REFRESH"]
    assert [row["id"] for row in result] == ["a", "b"]
    assert result[1]["cvs"] == 3.9


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), True, 6, -1, "4"])
def test_scoring_rejects_invalid_axis(invalid):
    candidate = {"id": "a", "concept": "A", "coverage_category": "frontier"}
    row = {"id": "a", **dict.fromkeys(score.AXES, 4), "rel": invalid,
           "rationale": "A specific operational research gap."}
    with pytest.raises(ValueError, match="invalid rel"):
        score.validate({"rows": [row]}, [candidate], WEIGHTS)


def test_scoring_rejects_duplicate_or_missing_ids():
    candidates = [{"id": value, "concept": value, "coverage_category": "frontier"} for value in ("a", "b")]
    row = {"id": "a", **dict.fromkeys(score.AXES, 4), "rationale": "A specific operational research gap."}
    with pytest.raises(ValueError, match="duplicate"):
        score.validate({"rows": [row, row]}, candidates, WEIGHTS)
    with pytest.raises(ValueError, match="exactly one"):
        score.validate({"rows": [row]}, candidates, WEIGHTS)


def test_half_point_axes_keep_the_precision_required_by_the_canonical_checker():
    candidate = {"id": "a", "concept": "A", "coverage_category": "frontier"}
    row = {"id": "a", "rel": 5, "use": 5, "nov": 4, "int": 4.5, "via": 5,
           "rationale": "A specific operational research gap."}
    assert score.validate({"rows": [row]}, [candidate], WEIGHTS)[0]["cvs"] == 4.725
