"""Ranked automation preserves queue identity and resumes without model calls."""
import importlib.util
import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ranked", ROOT / "scripts/codex_ranked_research.py")
ranked = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ranked)


def test_ranked_parser_keeps_literal_pipes_and_parent():
    rows = ranked.ranked_rows("| 1 | 4.2 | RESEARCH | A | B | Parent | dr | pending |")
    assert rows[0]["concept"] == "A|B"
    assert rows[0]["parent"] == "Parent"


def test_manifest_preserves_commas_collision_identity_and_resume(tmp_path):
    manifest = {"concepts": [{"name": "placeholder", "slug": "placeholder", "status": "pending"}]}
    saved = []
    shared = SimpleNamespace(run_lock=lambda slug: nullcontext(), load_manifest=lambda slug: manifest,
                             save_manifest=lambda value: saved.append(json.loads(json.dumps(value))),
                             write_draft=lambda value: None, slugify=lambda name: "same-slug")
    names = ["Read, write, and retry", "Other concept"]
    first = ranked.prepare_manifest(shared, "run", "Parent", names, tmp_path / "plan.json")
    assert [row["name"] for row in first["concepts"]] == names
    assert len({row["slug"] for row in first["concepts"]}) == 2
    first["concepts"][0]["status"] = "done"
    resumed = ranked.prepare_manifest(shared, "run", "Parent", ["changed"], tmp_path / "plan.json")
    assert resumed["concepts"][0]["status"] == "done"
    assert resumed["concepts"][0]["name"] == names[0]
    assert resumed["budget_minutes"] == 45


def test_queue_completion_marks_only_exact_names(tmp_path):
    queue = tmp_path / "concept-tree/RESEARCH_QUEUE.md"
    queue.parent.mkdir()
    queue.write_text("- [ ] Concept: `A, B` | Parent: `Root`\n- [ ] Concept: `A` | Parent: `Root`\n")
    shared = SimpleNamespace(RESEARCH_DIR=tmp_path / "research", locked=lambda path: nullcontext(),
                             atomic_write=lambda path, text: path.write_text(text))
    ranked.complete_queue(shared, tmp_path, ["A, B"])
    assert queue.read_text().splitlines() == ["- [x] Concept: `A, B` | Parent: `Root`", "- [ ] Concept: `A` | Parent: `Root`"]


def test_queue_completion_uses_planning_identity(tmp_path):
    queue = tmp_path / "concept-tree/RESEARCH_QUEUE.md"
    queue.parent.mkdir()
    queue.write_text("- [ ] Concept: `A,   B` | Parent: `Root`\n- [ ] Concept: `A, B extra`\n")
    shared = SimpleNamespace(RESEARCH_DIR=tmp_path / "research", locked=lambda path: nullcontext(),
                             atomic_write=lambda path, text: path.write_text(text))
    ranked.complete_queue(shared, tmp_path, ["a, b"])
    assert queue.read_text().splitlines() == ["- [x] Concept: `A,   B` | Parent: `Root`", "- [ ] Concept: `A, B extra`"]


def test_new_revisit_gets_a_fresh_identity():
    names = ["Previously researched"]
    assert ranked.cohort_id(names) == ranked.cohort_id(names)
    assert ranked.cohort_id(names, revisit=True) != ranked.cohort_id(names, revisit=True)


def test_adapter_setup_failure_releases_batch_checkout(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
    monkeypatch.setenv("HUB_DIR", str(tmp_path))
    monkeypatch.setenv("LLMS_EXPLORER_REPO", str(tmp_path))
    plan = tmp_path / "batch/plan.json"
    ranked.atomic(plan, {"cohorts": [{"id": "test", "status": "pending", "concepts": ["A"]}], "rows": []})
    def broken(*args):
        raise ImportError("shared runtime unavailable")
    monkeypatch.setattr(ranked, "load", broken)
    assert ranked.execute_locked(tmp_path, tmp_path, plan) == 1
    marker = json.loads((tmp_path / "home/.llmsx/jobs/batches/batch/run.json").read_text())
    assert marker["status"] == "needs-review"
    assert marker["concepts"] == []
    assert "runtime unavailable" in json.loads(plan.read_text())["error"]


def test_finalized_owned_cohort_resumes_site_even_when_covered_and_queue_done(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
    monkeypatch.setenv("HUB_DIR", str(tmp_path))
    monkeypatch.setenv("LLMS_EXPLORER_REPO", str(tmp_path))
    plan = tmp_path / "batch/plan.json"
    cohort = {"id": "test", "parent": "Root", "status": "needs-review", "concepts": ["A"], "error": "old failure"}
    ranked.atomic(plan, {"cohorts": [cohort], "rows": [{"concept": "A", "mode": "dr"}], "error": "old failure"})
    manifest = {"status": "finalized", "ranked_queue_source": str(plan),
                "concepts": [{"name": "A", "status": "done"}]}
    ranked.atomic(tmp_path / "research/test/manifest.json", manifest)
    queue = tmp_path / "concept-tree/RESEARCH_QUEUE.md"
    queue.parent.mkdir()
    queue.write_text("- [x] Concept: `A`\n")
    shared = SimpleNamespace(run_dir=lambda slug: tmp_path / "research" / slug,
                             run_lock=lambda slug: nullcontext(), load_manifest=lambda slug: manifest,
                             save_manifest=lambda value: None, write_draft=lambda value: None,
                             RESEARCH_DIR=tmp_path / "research", locked=lambda path: nullcontext(),
                             atomic_write=lambda path, text: path.write_text(text))
    tree = SimpleNamespace(load_queue=lambda path: [{"concept": "A", "done": True}],
                           load_nodes=lambda path: [{"concept": "A", "aliases": []}])
    def fake_load(name, path):
        if name == "ranked_adapter":
            return SimpleNamespace(load_shared=lambda: shared)
        if name == "cohort_checkouts":
            return SimpleNamespace(runs=list)
        return tree
    commands = []
    monkeypatch.setattr(ranked, "load", fake_load)
    monkeypatch.setattr(ranked, "run_command", lambda command, *args, **kwargs: commands.append(command))
    assert ranked.execute_locked(tmp_path, tmp_path, plan) == 0
    result = json.loads(plan.read_text())
    assert result["cohorts"][0]["status"] == "complete"
    assert "error" not in result
    assert "error" not in result["cohorts"][0]
    assert any("research_site_sync.py" in command[1] for command in commands)
    assert not any("research" in command[2:3] or "gate" in command[2:3] for command in commands)
