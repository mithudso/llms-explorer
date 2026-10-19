"""Concept Viability Score (CVS): stored with the concept, gating the auto-researchers.

The score is concept-family-explorer's 0-5 pre-research gate. It must live where the
tree, the site and the explorer can read it (a node field for researched concepts, a
sidecar for names with no node), and the unattended researchers must skip anything
below the floor.
"""

import json

import pytest

import concept_tree as ct

NODES = [
    {"concept": "Root", "skillId": None, "parentConcept": None,
     "childConcepts": ["High", "Low", "Unscored", "Done"],
     "researchedAt": "2026-08-01", "sourcesCount": 3, "conceptsCount": 2},
    {"concept": "Done", "skillId": None, "parentConcept": "Root", "childConcepts": [],
     "researchedAt": "2026-08-02", "sourcesCount": 2, "conceptsCount": 1,
     "cvs": 4.1, "cvsDecision": "RESEARCH", "cvsScoredAt": "2026-08-01", "cvsSubject": "root"},
]
QUEUE = """\
- [ ] Concept: `Queued High` | Parent: `Root` | Mode: `dr` | CVS: `3.85`
- [ ] Concept: `Queued Plain` | Parent: `Root`
"""
SCORES = {"High": {"cvs": 3.6, "decision": "RESEARCH"}, "Low": {"cvs": 2.1, "decision": "SKIP"}}


@pytest.fixture
def tree(tmp_path):
    q = tmp_path / "q.md"
    q.write_text(QUEUE)
    return ct.ConceptTree(NODES, ct.load_queue(q), scores=SCORES)


def test_queue_line_cvs_tag_is_parsed_and_optional(tmp_path):
    q = tmp_path / "q.md"
    q.write_text(QUEUE)
    by = {e["concept"]: e for e in ct.load_queue(q)}
    assert by["Queued High"]["cvs"] == 3.85 and by["Queued High"]["mode"] == "dr"
    assert by["Queued Plain"]["cvs"] is None


def test_queue_concept_writes_the_tag_and_old_lines_still_parse(tmp_path):
    q = tmp_path / "q.md"
    assert ct.queue_concept("Scored One", "Root", "dr", path=q, cvs=3.456)
    assert "| CVS: `3.46`" in q.read_text()
    assert ct.queue_concept("Plain One", path=q)
    assert [e["cvs"] for e in ct.load_queue(q)] == [3.46, None]


def test_a_node_carries_its_own_score_and_a_frontier_name_uses_the_sidecar(tree):
    assert tree.score("Done")["cvs"] == 4.1
    assert tree.score("Low")["cvs"] == 2.1           # frontier, from the sidecar
    assert tree.score("Unscored") is None
    assert tree.frontier["High"]["cvs"] == 3.6
    assert tree.frontier["Queued High"]["cvs"] == 3.85   # from the queue tag
    assert "cvs" not in tree.frontier["Unscored"]


def test_detail_exposes_the_score(tree):
    d = ct.detail(tree, "Done")
    assert d["cvs"] == 4.1 and d["cvsDecision"] == "RESEARCH"
    assert ct.detail(tree, "Low")["cvs"] == 2.1
    assert "cvs" not in ct.detail(tree, "Unscored")


def test_passes_cvs_is_inclusive_and_unscored_is_opt_in():
    assert ct.passes_cvs({"cvs": 3.2}, 3.2, False)
    assert not ct.passes_cvs({"cvs": 3.19}, 3.2, False)
    assert not ct.passes_cvs(None, 3.2, False)
    assert ct.passes_cvs(None, 3.2, True)
    assert ct.passes_cvs(None, None, False)             # no threshold: legacy behaviour


def test_gate_keeps_high_drops_low_and_unscored_and_reports_why(tree):
    rows = [{"concept": c} for c in ("High", "Low", "Unscored", "Queued High")]
    kept, rep = ct.gate_by_cvs(rows, tree, 3.2)
    assert [r["concept"] for r in kept] == ["High", "Queued High"]
    assert rep["skipped_below_cvs"] == 1 and rep["skipped_unscored"] == 1
    assert rep["lowest_skipped"] == ["2.10 Low"]
    kept2, _ = ct.gate_by_cvs(rows, tree, 3.2, include_unscored=True)
    assert [r["concept"] for r in kept2] == ["High", "Unscored", "Queued High"]
    kept3, rep3 = ct.gate_by_cvs(rows, tree, None)
    assert len(kept3) == 4 and rep3["skipped_below_cvs"] == 0


def test_telemetry_newest_row_wins_and_parent_suffix_maps_to_the_node(tmp_path):
    t = tmp_path / "t.jsonl"
    rows = [
        {"runner": "cfe", "concept": "Alpha", "cvs": 2.0, "decision": "SKIP", "date": "2026-10-01", "subject": "s1"},
        {"runner": "cfe", "concept": "Alpha", "cvs": 3.9, "decision": "RESEARCH", "date": "2026-10-09", "subject": "s2"},
        {"runner": "cfe", "concept": "Beta (parent)", "cvs": 4.6, "decision": "REFRESH", "date": "2026-10-05"},
        {"runner": "dr", "concept": "Gamma", "cvs": 5.0},                 # not a cfe row
        {"runner": "cfe", "topic": "run-level row"},                      # no concept
        "not json",
    ]
    t.write_text("\n".join(r if isinstance(r, str) else json.dumps(r) for r in rows))
    found = ct.scores_from_telemetry(t)
    assert set(found) == {"Alpha", "Beta"}
    assert found["Alpha"]["cvs"] == 3.9 and found["Alpha"]["subject"] == "s2"


def test_apply_scores_writes_nodes_and_sidecar_without_touching_other_fields():
    nodes = [dict(n) for n in NODES]
    scores: dict = {}
    n_nodes, n_side = ct.apply_scores(nodes, {
        "root": {"cvs": 3.0, "decision": "SKIP", "scoredAt": "2026-10-19", "subject": "x"},   # case-insensitive node match
        "Ghost": {"cvs": 3.3, "decision": "RESEARCH", "scoredAt": "2026-10-19", "subject": "x"},
        "Bad": {"cvs": None},
    }, scores)
    assert (n_nodes, n_side) == (1, 1)
    assert nodes[0]["cvs"] == 3.0 and nodes[0]["sourcesCount"] == 3
    assert scores["Ghost"]["cvs"] == 3.3 and "Bad" not in scores


def test_backfill_cli_round_trips_through_the_files(tmp_path, capsys):
    tree_p, scores_p, tel = tmp_path / "tree.json", tmp_path / "cvs-scores.json", tmp_path / "t.jsonl"
    tree_p.write_text(json.dumps([dict(NODES[0], cvs=None)]))
    tel.write_text(json.dumps({"runner": "cfe", "concept": "Root", "cvs": 3.7, "decision": "RESEARCH", "date": "2026-10-19"}) + "\n"
                   + json.dumps({"runner": "cfe", "concept": "Ghost", "cvs": 2.2, "decision": "SKIP", "date": "2026-10-19"}) + "\n")
    rc = ct.main(["scores", "backfill", "--telemetry", str(tel), "--tree", str(tree_p), "--scores", str(scores_p)])
    assert rc == 0
    assert json.loads(tree_p.read_text())[0]["cvs"] == 3.7
    assert ct.load_scores(scores_p)["Ghost"]["cvs"] == 2.2
    capsys.readouterr()
    ct.main(["scores", "backfill", "--telemetry", str(tel), "--tree", str(tree_p), "--scores", str(scores_p), "--dry-run"])
    assert json.loads(capsys.readouterr().out)["written"] is False


def test_default_gate_matches_the_family_explorer_floor():
    assert ct.DEFAULT_MIN_CVS == 3.2
