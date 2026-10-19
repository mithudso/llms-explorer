# llmsx/tests/test_explorer_cvs.py — the explorer shows the Concept Viability Score.
from __future__ import annotations

import json

from llmsx import explorer_store as es

NODES = [
    {"concept": "Scored", "slug": "scored", "parentConcept": None, "childConcepts": ["Ghost"],
     "skillId": None, "researchedAt": "2026-10-19", "sourcesCount": 4, "conceptsCount": 3,
     "cvs": 4.65, "cvsDecision": "RESEARCH", "cvsScoredAt": "2026-10-19"},
    {"concept": "Plain", "slug": "plain", "parentConcept": None, "childConcepts": [],
     "skillId": None, "researchedAt": "2026-10-19", "sourcesCount": 1, "conceptsCount": 1},
]


def _outline():
    return es.build_outline(NODES)


def test_tag_marks_scores_below_the_gate_and_hides_unscored():
    assert es.cvs_tag(4.65) == "4.65"
    assert es.cvs_tag(3.2) == "3.20"
    assert es.cvs_tag(2.1) == "2.10↓"
    assert es.cvs_tag(None) == ""


def test_researched_overview_shows_score_decision_and_date():
    md = es.overview_markdown(NODES[0], "Scored", _outline(), {}, "", False)
    assert "**viability (CVS):** 4.65 / 5 (RESEARCH), scored 2026-10-19" in md
    assert "viability" not in es.overview_markdown(NODES[1], "Plain", _outline(), {}, "", False)


def test_frontier_overview_explains_a_score_below_the_gate():
    low = es.overview_markdown(None, "Ghost", _outline(), {}, "", False, 2.4)
    assert "2.40 / 5" in low and "below the 3.2 research gate" in low
    ok = es.overview_markdown(None, "Ghost", _outline(), {}, "", False, 3.6)
    assert "3.60 / 5" in ok and "below" not in ok
    assert "viability" not in es.overview_markdown(None, "Ghost", _outline(), {}, "", False)


def test_load_scores_merges_sidecar_and_queue_tags_and_survives_missing_files(tmp_path):
    assert es.load_scores(tmp_path) == {}
    (tmp_path / "concept-tree").mkdir()
    (tmp_path / es.QUEUE_REL).write_text(
        "- [ ] Concept: `Queued` | Parent: `Scored` | Mode: `dr` | CVS: `3.45`\n"
        "- [ ] Concept: `Untagged` | Parent: `Scored`\n")
    (tmp_path / es.SCORES_REL).write_text(json.dumps({"Ghost": {"cvs": 2.4}, "Bad": "x"}))
    assert es.load_scores(tmp_path) == {"Queued": 3.45, "Ghost": 2.4}


def test_queue_tag_does_not_break_mode_or_cluster_parsing(tmp_path):
    (tmp_path / "concept-tree").mkdir()
    (tmp_path / es.QUEUE_REL).write_text(
        "- [ ] Concept: `A` | Parent: `P` | Mode: `dr` | CVS: `3.10` | Cluster: `fam`\n")
    (row,) = es.load_queue(tmp_path)
    assert (row["mode"], row["cvs"], row["cluster"]) == ("dr", 3.1, "fam")
    assert es.mark_queue_done(tmp_path, ["A"]) == 1
    assert "CVS: `3.10`" in (tmp_path / es.QUEUE_REL).read_text()          # ticking keeps the tag
