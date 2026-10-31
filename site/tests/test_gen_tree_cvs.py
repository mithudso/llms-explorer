# site/tests/test_gen_tree_cvs.py — the Concept Viability Score reaches the site's tree data.
# ruff: noqa: E501  -- fixture strings mirror real tree.json rows
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_tree  # noqa: E402

TREE = [
    {"concept": "Root", "skillId": None, "parentConcept": None, "childConcepts": ["Kid", "Scored Ghost", "Plain Ghost"],
     "researchedAt": "2026-08-01", "sourcesCount": 3, "conceptsCount": 9, "slug": "root", "aliases": [],
     "cvs": 4.65, "cvsDecision": "RESEARCH", "cvsScoredAt": "2026-10-19"},
    {"concept": "Kid", "skillId": None, "parentConcept": "Root", "childConcepts": [],
     "researchedAt": "2026-08-02", "sourcesCount": 1, "conceptsCount": 2, "slug": "kid", "aliases": []},
]


def _repo(tmp_path, queue=""):
    ct_dir = tmp_path / "concept-tree"
    ct_dir.mkdir(exist_ok=True)
    (ct_dir / "tree.json").write_text(json.dumps(TREE))
    (ct_dir / "cvs-scores.json").write_text(json.dumps({"Scored Ghost": {"cvs": 2.4, "decision": "SKIP"}}))
    (ct_dir / "RESEARCH_QUEUE.md").write_text(queue)
    return tmp_path


def test_a_researched_node_carries_its_score_and_an_unscored_one_has_no_key(tmp_path):
    out = gen_tree.build(_repo(tmp_path))
    assert out["nodes"]["root"]["cvs"] == 4.65
    assert out["nodes"]["root"]["cvsDecision"] == "RESEARCH"
    assert out["nodes"]["root"]["cvsScoredAt"] == "2026-10-19"
    assert "cvs" not in out["nodes"]["kid"]


def test_frontier_names_take_their_score_from_the_sidecar_or_the_queue_tag(tmp_path):
    out = gen_tree.build(_repo(tmp_path, "- [ ] Concept: `Queued One` | Parent: `Root` | CVS: `3.45`\n"))
    by = {f["concept"]: f for f in out["frontier"]}
    assert by["Scored Ghost"]["cvs"] == 2.4 and by["Scored Ghost"]["cvsDecision"] == "SKIP"
    assert by["Queued One"]["cvs"] == 3.45
    assert "cvs" not in by["Plain Ghost"]


def test_output_is_deterministic_with_scores(tmp_path):
    repo = _repo(tmp_path)
    a, b = gen_tree.build(repo), gen_tree.build(repo)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_frontier_reads_one_queue_snapshot_and_preserves_duplicate_precedence(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    reads = []
    rows = [{'concept': 'Queued', 'parentConcept': 'Root', 'cvs': 3.25},
            {'concept': 'Queued', 'parentConcept': 'Kid', 'cvs': 4.5},
            {'concept': 'Other', 'parentConcept': 'Root'}]
    def read_queue(path):
        reads.append(path)
        return rows
    monkeypatch.setattr(gen_tree, 'queue_frontier', read_queue)
    frontier = {row['concept']: row for row in gen_tree.build(repo)['frontier']}
    assert reads == [repo], 'a large frontier must not repeatedly parse the complete queue'
    assert frontier['Queued']['parent'] == 'Kid'
    assert frontier['Queued']['cvs'] == 3.25
    assert frontier['Other']['parent'] == 'Root'
