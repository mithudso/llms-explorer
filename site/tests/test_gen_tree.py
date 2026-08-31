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
    assert out["frontier"] == [{"concept": "Ghost", "parent": "Root", "parent_slug": "root",
                                "source": "child-reference"}]
    assert [c["state"] for c in out["nodes"]["root"]["children"]] == ["researched", "frontier"]
    assert out["nodes"]["kid"]["parent_slug"] == "root"
    assert out["nodes"]["root"]["aliases"] == ["Roots"]
    assert out["nodes"]["root"]["state"] == "researched"


def test_generated_stamp_and_stable_ordering(tmp_path):
    out = gen_tree.build(_repo(tmp_path))
    assert len(out["generated"]) == 10 and out["generated"][4] == "-"
    again = gen_tree.build(_repo(tmp_path))
    assert json.dumps(out, sort_keys=True) == json.dumps(again, sort_keys=True)


def test_the_stamp_is_the_newest_fact_not_the_clock(tmp_path):
    """CI regenerates this file and byte-diffs it against the committed copy, so
    a wall-clock stamp turned every push after the commit date red with no data
    change at all. `generated` is the newest researchedAt in the source."""
    out = gen_tree.build(_repo(tmp_path))
    assert out["generated"] == "2026-08-02"                # max researchedAt in TREE
    newer = [dict(TREE[0]), dict(TREE[1], researchedAt="2026-09-09")]
    (tmp_path / "concept-tree" / "tree.json").write_text(json.dumps(newer))
    assert gen_tree.build(tmp_path)["generated"] == "2026-09-09"


def test_frontier_unions_the_research_queue(tmp_path):
    """Spec 09 §3: frontier = unresearched childConcepts UNION the unchecked
    lines of concept-tree/RESEARCH_QUEUE.md. Only the first half was built, so
    the first queued concept would have made the site disagree with the TUI."""
    repo = _repo(tmp_path)
    (repo / "concept-tree" / "RESEARCH_QUEUE.md").write_text(
        "# Queue\n\n"
        "- [ ] Concept: `Queued` | Parent: `Root`\n"
        "- [ ] Concept: `Orphan`\n"
        "- [x] Concept: `Done` | Parent: `Root`\n"
        "- [ ] Concept: `Kid` | Parent: `Root`\n")          # already researched: not frontier
    front = {f["concept"]: f for f in gen_tree.build(repo)["frontier"]}
    assert set(front) == {"Ghost", "Queued", "Orphan"}
    assert front["Queued"]["parent"] == "Root" and front["Queued"]["parent_slug"] == "root"
    assert front["Orphan"]["parent"] is None                # the pages' unparented bucket
    assert front["Queued"]["source"] == "research-queue"
    assert front["Ghost"]["source"] == "child-reference"


def test_a_child_reference_wins_over_a_queue_line(tmp_path):
    """ConceptTree._derive_frontier prefers the tree's own child reference for
    the parent; the site must not disagree about the same concept's parent."""
    repo = _repo(tmp_path)
    (repo / "concept-tree" / "RESEARCH_QUEUE.md").write_text(
        "- [ ] Concept: `Ghost` | Parent: `Elsewhere`\n")
    ghost = [f for f in gen_tree.build(repo)["frontier"] if f["concept"] == "Ghost"][0]
    assert ghost["parent"] == "Root" and ghost["source"] == "child-reference"


def test_skill_summary_comes_from_the_vendored_skill_or_map(tmp_path):
    """09 §3's renderer contract wants a description per node; it shipped empty
    on all 37. Read from this repo's skills/ (never ~/.claude, which CI has
    not got), else from the map the snapshot refresh vendors."""
    repo = _repo(tmp_path)
    (repo / "skills" / "root-skill").mkdir(parents=True)
    (repo / "skills" / "root-skill" / "SKILL.md").write_text(
        "---\nname: root-skill\n---\n\n# Heading\n\nWhat the root skill does.\n")
    (repo / "concept-tree" / "skill-summaries.json").write_text(
        json.dumps({"root-skill": "from the map", "other": "x" * 900}))
    nodes = gen_tree.build(repo)["nodes"]
    assert nodes["root"]["skillSummary"] == "What the root skill does."   # the file wins
    assert nodes["kid"]["skillSummary"] == ""                             # no skillId
    assert len(gen_tree._skill_summaries(repo)["other"]) == gen_tree.SKILL_SUMMARY_CHARS


def test_the_real_tree_describes_the_nodes_whose_skill_is_vendored():
    out = gen_tree.build(SITE.parent)
    described = [n for n in out["nodes"].values() if n["skillSummary"]]
    assert described, "no node carries a description — skills/ and the summary map are both empty"
    assert all(len(n["skillSummary"]) <= gen_tree.SKILL_SUMMARY_CHARS for n in described)


def test_real_tree_builds():
    out = gen_tree.build(SITE.parent)
    assert len(out["nodes"]) >= 30 and len(out["roots"]) >= 1
    assert all(n["slug"] for n in out["nodes"].values())
