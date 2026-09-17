"""Compiled llms-concepts packs become concept-tree nodes (register_concept_packs)."""

import json
from pathlib import Path

import concept_tree as ct
import register_concept_packs as reg

ROOT = reg.FALLBACK_ROOT


def _pack(root: Path, slug: str, concept: str, *, kind: str = "concept",
          generated: str = "2026-09-02", sources=None, inputs=None) -> Path:
    d = root / f"{slug}.llms"
    d.mkdir(parents=True)
    manifest = {
        "kind": kind, "concept": concept, "slug": slug, "generated": generated,
        "sources": {"a.md": 3, "b.md": 1} if sources is None else sources,
        "inputs": ["/Users/x/a.md", "/Users/x/b.md"] if inputs is None else inputs,
        "facets": {"facts": 4},
    }
    (d / "manifest.json").write_text(json.dumps(manifest))
    (d / "llms.txt").write_text(f"# {concept}\n")
    return d


def _node(concept: str, parent: str | None = None, children=(), **extra) -> dict:
    n = {"concept": concept, "skillId": None, "parentConcept": parent,
         "childConcepts": list(children), "researchedAt": "2026-08-01",
         "sourcesCount": 1, "conceptsCount": len(children),
         "slug": ct.slugify(concept), "aliases": []}
    n.update(extra)
    return n


def _tree(nodes, queue_text: str | None = None, tmp_path: Path | None = None) -> ct.ConceptTree:
    queue = []
    if queue_text is not None:
        q = tmp_path / "RESEARCH_QUEUE.md"
        q.write_text(queue_text)
        queue = ct.load_queue(q)
    return ct.ConceptTree(nodes, queue)


def _changes(actions):
    return [(a["action"], a["concept"], a["parent"]) for a in actions if a["action"] != "skip"]


def test_registers_pack_under_its_default_parent(tmp_path):
    _pack(tmp_path, "prompt-caching", "Prompt caching")
    tree = _tree([_node(ROOT), _node("LLM Models and APIs")])

    actions = reg.plan(tree, reg.load_packs(tmp_path),
                       defaults={"Prompt caching": "LLM Models and APIs"})

    assert _changes(actions) == [("register", "Prompt caching", "LLM Models and APIs")]


def test_queue_parent_wins_over_default_when_it_is_a_node(tmp_path):
    _pack(tmp_path, "really-simple-licensing", "Really Simple Licensing (RSL)")
    tree = _tree(
        [_node(ROOT), _node("Document & File Formats"), _node("Other")],
        "- [ ] Concept: `Really Simple Licensing (RSL)` | Parent: `Document & File Formats`"
        " | Pack: x\n",
        tmp_path,
    )

    actions = reg.plan(tree, reg.load_packs(tmp_path),
                       defaults={"Really Simple Licensing (RSL)": "Other"})

    assert _changes(actions) == [
        ("register", "Really Simple Licensing (RSL)", "Document & File Formats")]


def test_child_reference_parent_wins_over_default(tmp_path):
    _pack(tmp_path, "indexing--databases", "Indexing")
    tree = _tree([_node(ROOT), _node("Databases", children=["Indexing"]), _node("Other")])

    actions = reg.plan(tree, reg.load_packs(tmp_path), defaults={"Indexing": "Other"})

    assert _changes(actions) == [("register", "Indexing", "Databases")]


def test_member_pack_waits_for_its_family_pack_registered_in_the_same_run(tmp_path):
    _pack(tmp_path, "agents-md-ucp", "agents.md and UCP")
    _pack(tmp_path, "llms-txt-family", "The family", kind="family")
    tree = _tree([_node(ROOT), _node("llms.txt root")])

    actions = reg.plan(tree, reg.load_packs(tmp_path),
                       defaults={"The family": "llms.txt root", "agents.md and UCP": "The family"})

    assert _changes(actions) == [("register", "The family", "llms.txt root"),
                                 ("register", "agents.md and UCP", "The family")]


def test_unknown_pack_falls_back_to_the_corpus_root(tmp_path):
    _pack(tmp_path, "onchain-fx-market-mechanics", "On-chain and FX market mechanics")
    tree = _tree([_node(ROOT)])

    actions = reg.plan(tree, reg.load_packs(tmp_path), defaults={})

    assert _changes(actions) == [("register", "On-chain and FX market mechanics", ROOT)]


def test_skips_eval_fixture_packs_built_from_temp_inputs(tmp_path):
    _pack(tmp_path, "heart", "Heart", inputs=["/private/tmp/lca-eval/anatomy-ch12.md"])
    tree = _tree([_node(ROOT)])

    (action,) = reg.plan(tree, reg.load_packs(tmp_path))

    assert action["action"] == "skip"
    assert "fixture" in action["reason"]


def test_load_packs_ignores_dirs_that_are_not_concept_packs(tmp_path):
    _pack(tmp_path, "prompt-caching", "Prompt caching")
    (tmp_path / "notes.md").write_text("not a pack")
    stray = tmp_path / "report-index.llms"
    stray.mkdir()
    report_index = {"kind": "report-index", "concept": "X", "slug": "x"}
    (stray / "manifest.json").write_text(json.dumps(report_index))
    (stray / "llms.txt").write_text("# X\n")

    assert [p.slug for p in reg.load_packs(tmp_path)] == ["prompt-caching"]


def test_apply_writes_node_fields_links_parent_and_backs_up(tmp_path):
    packs = tmp_path / "llms-concepts"
    _pack(packs, "prompt-caching", "Prompt caching", generated="2026-08-31",
          sources={"a.md": 2, "b.md": 5, "c.md": 1})
    tree_path = tmp_path / "tree.json"
    ct.save_nodes([_node(ROOT), _node("LLM Models and APIs")], tree_path)
    tree = ct.ConceptTree.load(tree_path, tmp_path / "no-queue.md", tmp_path / "no-state.json")
    actions = reg.plan(tree, reg.load_packs(packs),
                       defaults={"Prompt caching": "LLM Models and APIs"})

    new_problems = reg.apply(actions, tree_path, backup_path=tmp_path / "tree.json.bak")

    assert new_problems == []
    nodes = {n["concept"]: n for n in ct.load_nodes(tree_path)}
    node = nodes["Prompt caching"]
    assert node["parentConcept"] == "LLM Models and APIs"
    assert node["llmsFile"] == "llms-concepts/prompt-caching.llms/llms.txt"
    assert node["slug"] == "prompt-caching"
    assert node["researchedAt"] == node["firstResearchedAt"] == "2026-08-31"
    assert node["sourcesCount"] == 3
    assert node["skillId"] is None
    assert node["childConcepts"] == [] and node["conceptsCount"] == 0
    assert "Prompt caching" in nodes["LLM Models and APIs"]["childConcepts"]
    assert json.loads((tmp_path / "tree.json.bak").read_text())[0]["concept"] == ROOT


def test_second_run_plans_no_changes(tmp_path):
    packs = tmp_path / "llms-concepts"
    _pack(packs, "prompt-caching", "Prompt caching")
    tree_path = tmp_path / "tree.json"
    ct.save_nodes([_node(ROOT)], tree_path)
    tree = ct.ConceptTree.load(tree_path, tmp_path / "q.md", tmp_path / "s.json")
    reg.apply(reg.plan(tree, reg.load_packs(packs), defaults={}), tree_path, backup_path=None)

    tree = ct.ConceptTree.load(tree_path, tmp_path / "q.md", tmp_path / "s.json")
    actions = reg.plan(tree, reg.load_packs(packs), defaults={})

    assert _changes(actions) == []
    assert actions[0]["reason"].startswith("already registered")


def test_existing_node_missing_llms_file_is_repaired_in_place(tmp_path):
    packs = tmp_path / "llms-concepts"
    _pack(packs, "prompt-caching", "Prompt caching", generated="2026-08-31")
    tree_path = tmp_path / "tree.json"
    ct.save_nodes([_node(ROOT, children=["Prompt caching"]),
                   _node("Prompt caching", parent=ROOT, researchedAt="2026-07-01")], tree_path)
    tree = ct.ConceptTree.load(tree_path, tmp_path / "q.md", tmp_path / "s.json")

    actions = reg.plan(tree, reg.load_packs(packs), defaults={"Prompt caching": "Other"})
    assert _changes(actions) == [("repair", "Prompt caching", ROOT)]

    reg.apply(actions, tree_path, backup_path=None)
    node = {n["concept"]: n for n in ct.load_nodes(tree_path)}["Prompt caching"]
    assert node["llmsFile"] == "llms-concepts/prompt-caching.llms/llms.txt"
    assert node["parentConcept"] == ROOT
    assert node["researchedAt"] == "2026-07-01"


def test_cli_is_a_dry_run_unless_apply_is_passed(tmp_path, capsys):
    (tmp_path / "concept-tree").mkdir()
    tree_path = tmp_path / "concept-tree" / "tree.json"
    ct.save_nodes([_node(ROOT)], tree_path)
    _pack(tmp_path / "llms-concepts", "onchain-fx-market-mechanics",
          "On-chain and FX market mechanics")
    before = tree_path.read_text()

    assert reg.main(["--hub-dir", str(tmp_path)]) == 0
    assert tree_path.read_text() == before
    assert "dry run" in capsys.readouterr().out

    assert reg.main(["--hub-dir", str(tmp_path), "--apply"]) == 0
    assert "On-chain and FX market mechanics" in {n["concept"] for n in ct.load_nodes(tree_path)}
    assert list((tmp_path / "concept-tree").glob("tree.json.bak-*"))


def test_cli_parent_override_beats_every_other_signal(tmp_path):
    (tmp_path / "concept-tree").mkdir()
    tree_path = tmp_path / "concept-tree" / "tree.json"
    ct.save_nodes([_node(ROOT), _node("Databases", children=["Indexing"]), _node("Chosen")],
                  tree_path)
    _pack(tmp_path / "llms-concepts", "indexing--databases", "Indexing")

    assert reg.main(["--hub-dir", str(tmp_path), "--apply", "--parent", "Indexing=Chosen"]) == 0

    node = {n["concept"]: n for n in ct.load_nodes(tree_path)}["Indexing"]
    assert node["parentConcept"] == "Chosen"


def test_cli_rejects_a_parent_override_that_is_not_a_node(tmp_path, capsys):
    (tmp_path / "concept-tree").mkdir()
    ct.save_nodes([_node(ROOT)], tmp_path / "concept-tree" / "tree.json")
    _pack(tmp_path / "llms-concepts", "indexing--databases", "Indexing")

    assert reg.main(["--hub-dir", str(tmp_path), "--apply", "--parent", "Indexing=Nope"]) == 2
    assert "Nope" in capsys.readouterr().err
