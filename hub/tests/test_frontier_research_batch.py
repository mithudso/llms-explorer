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
