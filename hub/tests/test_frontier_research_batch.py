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
