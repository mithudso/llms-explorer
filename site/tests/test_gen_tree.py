# site/tests/test_gen_tree.py
# ruff: noqa: E501  -- fixture strings mirror real tree.json rows
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_tree  # noqa: E402

TREE = [
    {"concept": "Root", "skillId": "root-skill", "parentConcept": None,
     "childConcepts": ["Kid", "Ghost"], "researchedAt": "2026-08-01",
     "sourcesCount": 3, "conceptsCount": 9, "slug": "root", "aliases": ["Roots"]},
    {"concept": "Kid", "skillId": None, "parentConcept": "Root", "childConcepts": [],
     "researchedAt": "2026-08-02", "sourcesCount": 1, "conceptsCount": 2, "slug": "kid", "aliases": []},
]


def _repo(tmp_path):
    (tmp_path / "concept-tree").mkdir(exist_ok=True)  # called twice per test; stay idempotent
    (tmp_path / "concept-tree" / "tree.json").write_text(json.dumps(TREE))
    return tmp_path


def test_nodes_edges_and_derived_frontier(tmp_path):
    out = gen_tree.build(_repo(tmp_path))
    assert out["roots"] == ["root"]
    assert set(out["nodes"]) == {"root", "kid"}
    assert out["edges"] == [["root", "kid"]]
    # "Ghost" is named as a child but has no node of its own -> frontier, derived
    assert out["frontier"] == [{"concept": "Ghost", "parent": "Root", "parent_slug": "root"}]
    assert [c["state"] for c in out["nodes"]["root"]["children"]] == ["researched", "frontier"]
    assert out["nodes"]["kid"]["parent_slug"] == "root"
    assert out["nodes"]["root"]["aliases"] == ["Roots"]
    assert out["nodes"]["root"]["state"] == "researched"


def test_generated_stamp_and_stable_ordering(tmp_path):
    out = gen_tree.build(_repo(tmp_path))
    assert len(out["generated"]) == 10 and out["generated"][4] == "-"
    again = gen_tree.build(_repo(tmp_path))
    assert json.dumps(out, sort_keys=True) == json.dumps(again, sort_keys=True)


def test_real_tree_builds():
    out = gen_tree.build(SITE.parent)
    assert len(out["nodes"]) >= 30 and len(out["roots"]) >= 1
    assert all(n["slug"] for n in out["nodes"].values())
