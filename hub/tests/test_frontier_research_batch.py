"""Tests for the resumable frontier research runner's safety gates."""

from types import SimpleNamespace

import pytest

import frontier_research_batch as batch


def test_run_claude_pauses_on_provider_weekly_limit(monkeypatch, tmp_path):
    monkeypatch.setattr(batch.shutil, "which", lambda _: "/bin/claude")
    monkeypatch.setattr(
        batch.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1, stdout="You've hit your weekly limit", stderr=""
        ),
    )

    with pytest.raises(batch.BatchPaused, match="weekly limit"):
        batch.run_claude("prompt", tmp_path, 1)


def test_parent_for_preserves_known_parent():
    tree = SimpleNamespace(by_concept={"Known Parent": {}})
    front = {"concept": "A frontier concept", "parentConcept": "Known Parent"}

    assert batch.parent_for(front, tree) == "Known Parent"


def test_run_slug_separates_exact_names_with_casefold_collision():
    assert batch.slug("Multi-Document Transactions") == batch.slug("Multi-document Transactions")
    assert batch.run_slug("Multi-Document Transactions") != batch.run_slug(
        "Multi-document Transactions")


def test_batch_slug_assigns_tree_and_pack_names_in_stable_order(monkeypatch, tmp_path):
    import json

    names = ["Multi-document Transactions", "Multi-Document Transactions"]
    (tmp_path / "frontier.json").write_text(json.dumps([{"concept": n} for n in names]))
    tree = SimpleNamespace(by_concept={}, nodes=[])
    monkeypatch.setattr(batch.ct.ConceptTree, "load", lambda: tree)

    assert batch.batch_slug("Multi-Document Transactions", tmp_path) == batch.slug(names[1])
    assert batch.batch_slug("Multi-document Transactions", tmp_path) == (
        batch.slug(names[1]) + "-2")


def test_firecrawl_cache_filename_matches_cli_output():
    assert batch._firecrawl_filename(
        "https://www.mongodb.com/docs/atlas/atlas-resource-policies/") == (
            "mongodb.com-docs-atlas-atlas-resource-policies.md")


def test_parent_url_filter_rejects_templates_and_reuses_prior_failures():
    facts = """https://www.mongodb.com/docs/manual/ https://<host>/docs
https://api.example.com/data https://cloud.mongodb.com/api/{groupId}
https://github.com/mongodb/mongodb-kubernetes-operator"""
    assert batch._parent_urls(facts) == [
        "https://www.mongodb.com/docs/manual/",
        "https://github.com/mongodb/mongodb-kubernetes-operator",
    ]
    assert batch._failed_source_urls({
        "failedUrls": ["https://a.mongodb.com/404"],
        "failures": ["Firecrawl did not save https://b.mongodb.com/404"],
    }) == {"https://a.mongodb.com/404", "https://b.mongodb.com/404"}


def test_parent_reference_path_resolves_only_inside_a_trusted_skill_root(
        monkeypatch, tmp_path):
    skill_root = tmp_path / "skills"
    target = skill_root / "mongodb-atlas-expert" / "references" / "operator.md"
    target.parent.mkdir(parents=True)
    target.write_text("parent facts")
    outside = tmp_path / "outside.md"
    outside.write_text("outside")
    fake_tree = SimpleNamespace(by_concept={
        "Parent": {"skillId": "mongodb-atlas-expert/references/operator.md"},
        "Bad Parent": {"skillId": "../outside.md"},
    })
    monkeypatch.setattr(batch.ct.ConceptTree, "load", lambda: fake_tree)

    assert batch._parent_reference_path("Parent", (skill_root,)) == target
    assert batch._parent_reference_path("Bad Parent", (skill_root,)) is None


def test_parent_for_assigns_orphaned_compliance_concept():
    tree = SimpleNamespace(by_concept={"Data Ethics and Privacy": {}})
    front = {
        "concept": "EU AI Act Article 53(1)(c) TDM Opt-Out",
        "parentConcept": "Missing path",
    }

    assert batch.parent_for(front, tree) == "Data Ethics and Privacy"


def test_save_role_report_preserves_a_report_the_subagent_wrote_itself(tmp_path):
    path = tmp_path / "mechanism.md"
    path.write_text("x" * (batch.MIN_REPORT_BYTES + 1), encoding="utf-8")

    status = batch._save_role_report(path, "Report written. 40 atomic claims.")

    assert status == "written"
    assert path.read_text(encoding="utf-8") == "x" * (batch.MIN_REPORT_BYTES + 1)
    assert "Report written" in path.with_suffix(".summary.txt").read_text(encoding="utf-8")


def test_save_role_report_falls_back_when_subagent_wrote_nothing(tmp_path):
    path = tmp_path / "mechanism.md"

    status = batch._save_role_report(path, "Report written. 40 atomic claims.")

    assert "fallback" in status
    assert path.read_text(encoding="utf-8") == "Report written. 40 atomic claims.\n"


def test_filter_frontier_keeps_only_the_named_concepts_in_order(capsys):
    frontier = [
        {"concept": "A", "parent": None},
        {"concept": "B", "parent": None},
        {"concept": "C", "parent": None},
    ]

    kept = batch.filter_frontier(frontier, {"A", "C"})

    assert [f["concept"] for f in kept] == ["A", "C"]
    assert capsys.readouterr().err == ""


def test_filter_frontier_warns_on_a_requested_name_not_in_the_frontier(capsys):
    frontier = [{"concept": "A", "parent": None}]

    kept = batch.filter_frontier(frontier, {"A", "Not Queued"})

    assert [f["concept"] for f in kept] == ["A"]
    assert "Not Queued" in capsys.readouterr().err


def test_register_does_not_mislabel_new_node_with_the_rabbithole_skill(tmp_path):
    tree_path = tmp_path / "tree.json"
    tree_path.write_text(
        '[{"concept": "Known Parent", "childConcepts": [], "aliases": []}]',
        encoding="utf-8",
    )
    result = {"concept": "New Concept", "parent": "Known Parent",
              "status": "complete", "sources": 5}

    batch.register(result, tree_path, tmp_path / "backup")

    import json
    nodes = json.loads(tree_path.read_text(encoding="utf-8"))
    by = {n["concept"]: n for n in nodes}
    assert by["New Concept"]["skillId"] is None
    assert "New Concept" in by["Known Parent"]["childConcepts"]


def test_run_batch_parallel_registers_every_concept(monkeypatch, tmp_path):
    import json
    import time

    tree_path = tmp_path / "tree.json"
    tree_path.write_text('[{"concept": "P", "childConcepts": [], "aliases": []}]',
                         encoding="utf-8")

    def fake_research(concept, parent, run_dir, repo, timeout, inherited=None):
        time.sleep(0.01)
        return {"concept": concept, "parent": parent, "status": "complete", "sources": 3}

    monkeypatch.setattr(batch, "research_one", fake_research)
    pending = [(f"C{i}", "P") for i in range(12)]

    assert batch.run_batch(pending, tmp_path, tmp_path, 1, tree_path, jobs=4) == 0

    by = {n["concept"]: n for n in json.loads(tree_path.read_text(encoding="utf-8"))}
    assert all(f"C{i}" in by for i in range(12))
    assert len(by["P"]["childConcepts"]) == 12
    lines = (tmp_path / "results.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 12


def test_run_batch_stops_starting_concepts_after_a_pause(monkeypatch, tmp_path):
    tree_path = tmp_path / "tree.json"
    tree_path.write_text("[]", encoding="utf-8")
    started = []

    def fake_research(concept, parent, run_dir, repo, timeout, inherited=None):
        started.append(concept)
        raise batch.BatchPaused("weekly limit")

    monkeypatch.setattr(batch, "research_one", fake_research)
    pending = [(f"C{i}", None) for i in range(5)]

    assert batch.run_batch(pending, tmp_path, tmp_path, 1, tree_path, jobs=1) == 2
    assert started == ["C0"]
    assert not (tmp_path / "results.jsonl").exists()
