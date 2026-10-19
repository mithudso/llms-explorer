"""frontier_research_batch.py must not research a frontier concept below the CVS floor."""

import json
import sys

import pytest

import concept_tree as ct
import frontier_research_batch as frb

NODES = [
    {"concept": "Root", "skillId": None, "parentConcept": None,
     "childConcepts": ["Worth It", "Not Worth It", "Never Scored"],
     "researchedAt": "2026-08-01", "sourcesCount": 3, "conceptsCount": 2},
]


@pytest.fixture
def hub(tmp_path, monkeypatch):
    (tmp_path / "concept-tree").mkdir()
    (tmp_path / "concept-tree" / "tree.json").write_text(json.dumps(NODES))
    (tmp_path / "concept-tree" / "RESEARCH_QUEUE.md").write_text("")
    (tmp_path / "concept-tree" / "cvs-scores.json").write_text(json.dumps(
        {"Worth It": {"cvs": 3.8}, "Not Worth It": {"cvs": 2.4}}))
    monkeypatch.setattr(ct, "HUB_DIR", tmp_path)
    monkeypatch.setattr(ct, "TREE_PATH", tmp_path / "concept-tree" / "tree.json")
    monkeypatch.setattr(ct, "QUEUE_PATH", tmp_path / "concept-tree" / "RESEARCH_QUEUE.md")
    monkeypatch.setattr(ct, "SCORES_PATH", tmp_path / "concept-tree" / "cvs-scores.json")
    monkeypatch.setattr(ct, "RESEARCH_STATE_PATH", tmp_path / "concept-tree" / "research_state.json")
    monkeypatch.setattr(frb, "prepare_parent_contexts", lambda *a, **k: {})
    return tmp_path


def _run(monkeypatch, hub, *argv):
    seen = {}

    def fake_batch(pending, *a, **k):
        seen["pending"] = [c for c, _p in pending]
        return 0

    monkeypatch.setattr(frb, "run_batch", fake_batch)
    monkeypatch.setattr(sys, "argv", ["frb", "--repo", str(hub), "--run-dir", str(hub / "run"), *argv])
    assert frb.main() == 0
    return seen["pending"]


def test_default_gate_researches_only_concepts_at_or_above_the_floor(hub, monkeypatch, capsys):
    assert _run(monkeypatch, hub) == ["Worth It"]
    err = capsys.readouterr().err
    assert '"skipped_below_cvs": 1' in err and '"skipped_unscored": 1' in err


def test_include_unscored_adds_the_never_scored_but_not_the_low_scored(hub, monkeypatch):
    assert _run(monkeypatch, hub, "--include-unscored") == ["Never Scored", "Worth It"]


def test_zero_disables_the_gate(hub, monkeypatch):
    assert _run(monkeypatch, hub, "--min-cvs", "0") == ["Never Scored", "Not Worth It", "Worth It"]


def test_a_stricter_floor_is_honoured(hub, monkeypatch):
    assert _run(monkeypatch, hub, "--min-cvs", "3.9") == []
