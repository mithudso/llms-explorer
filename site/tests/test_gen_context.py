# site/tests/test_gen_context.py — the context-file index files every file and pack.
# ruff: noqa: E501
import json
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE / "tools"))
import gen_context  # noqa: E402

TREE = {
    "generated": "2026-09-20",
    "roots": ["alpha", "beta"],
    "nodes": {
        "alpha": {"slug": "alpha", "concept": "Alpha", "parent_slug": None},
        "alpha-kid": {"slug": "alpha-kid", "concept": "Alpha kid", "parent_slug": "alpha"},
        "beta": {"slug": "beta", "concept": "Beta", "parent_slug": None},
    },
}


def _pack(slug, concept, facts):
    return {"slug": slug, "concept": concept, "generated": "2026-09-19", "summary": "s",
            "facets": [{"title": "F", "facts": [{"text": t, "source": s, "note": None} for t, s in facts]}],
            "related": []}


def _fixture(tmp_path):
    sources = tmp_path / "sources"
    (sources / "hub").mkdir(parents=True)
    (sources / "hub" / "shared.md").write_text("---\ntitle: 'Shared report'\ndescription: 'Cited twice.'\n---\n\nbody\n")
    (sources / "hub" / "lonely.md").write_text("---\ntitle: 'Lonely report'\n---\n\nnobody cites me\n")
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    shared = "https://llms-explorer.com/sources/hub/shared/#x"
    (concepts / "alpha-kid.json").write_text(json.dumps(_pack("alpha-kid", "Alpha kid", [("a", shared), ("b", shared), ("c", "https://other.example/")])))
    (concepts / "beta.json").write_text(json.dumps(_pack("beta", "Beta", [("d", shared)])))
    (concepts / "orphan.json").write_text(json.dumps(_pack("orphan", "Orphan", [("e", "~/local.md")])))
    tree = tmp_path / "tree.json"
    tree.write_text(json.dumps(TREE))
    return sources, concepts, tree


def test_files_and_packs_are_filed_under_roots(tmp_path):
    out = gen_context.build(*_fixture(tmp_path))
    by_slug = {r["slug"]: r for r in out["roots"]}
    # the shared file is cited twice from alpha's subtree and once from beta: alpha wins
    alpha_files = {f["name"] for f in by_slug["alpha"]["files"]}
    assert alpha_files == {"shared"}
    shared = by_slug["alpha"]["files"][0]
    assert shared["concepts"] == ["alpha-kid", "beta"], "most-citing concept first"
    assert shared["download"] == "/downloads/sources/hub/shared.md"
    assert shared["route"] == "/sources/hub/shared/"
    assert shared["title"] == "Shared report" and shared["description"] == "Cited twice."
    # a pack goes under its own root, walked up parent_slug
    assert [c["slug"] for c in by_slug["alpha"]["concepts"]] == ["alpha-kid"]
    assert by_slug["alpha"]["concepts"][0]["facts"] == 3
    assert by_slug["alpha"]["concepts"][0]["download"] == "/downloads/concepts/alpha-kid.md"
    assert [c["slug"] for c in by_slug["beta"]["concepts"]] == ["beta"]


def test_nothing_is_invisible(tmp_path):
    """An uncited file and a pack the tree cannot place both land under `unfiled`, last."""
    out = gen_context.build(*_fixture(tmp_path))
    assert out["roots"][-1]["slug"] == "unfiled"
    unfiled = out["roots"][-1]
    assert [f["name"] for f in unfiled["files"]] == ["lonely"]
    assert [c["slug"] for c in unfiled["concepts"]] == ["orphan"]
    assert out["totals"] == {"files": 2, "bytes": unfiled["files"][0]["bytes"] + out["roots"][0]["files"][0]["bytes"],
                             "concepts": 3, "facets": 3, "facts": 5, "roots": 2}


def test_generated_comes_from_the_tree_and_output_is_stable(tmp_path):
    fx = _fixture(tmp_path)
    first = gen_context.build(*fx)
    assert first["generated"] == "2026-09-20"
    out1, out2 = tmp_path / "a.json", tmp_path / "b.json"
    gen_context.write(first, out1)
    gen_context.write(gen_context.build(*fx), out2)
    assert out1.read_bytes() == out2.read_bytes()


def test_a_parent_cycle_ends_the_walk():
    nodes = {"a": {"parent_slug": "b"}, "b": {"parent_slug": "a"}}
    assert gen_context.root_of("a", nodes) in {"a", "b"}
    assert gen_context.root_of("ghost", nodes) is None


def test_the_committed_index_matches_the_committed_inputs():
    """context.json is generated and committed (like tree.json): a stale copy would
    list files that are gone or miss packs that landed."""
    committed = SITE / "src" / "data" / "context.json"
    if not committed.is_file():
        import pytest
        pytest.skip("no committed context.json")
    fresh = gen_context.build(gen_context.DEFAULT_SOURCES, gen_context.DEFAULT_CONCEPTS, gen_context.DEFAULT_TREE)
    assert json.loads(committed.read_text()) == fresh, "run site/tools/gen_context.py and commit the result"
