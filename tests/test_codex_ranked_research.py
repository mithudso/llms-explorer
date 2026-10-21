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
    monkeypatch.delenv("LLMSX_HOME", raising=False)
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
    monkeypatch.delenv("LLMSX_HOME", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
    monkeypatch.setenv("HUB_DIR", str(tmp_path))
    monkeypatch.setenv("LLMS_EXPLORER_REPO", str(tmp_path))
    plan = tmp_path / "batch/plan.json"
    cohort = {"id": "test", "parent": "Root", "status": "needs-review", "concepts": ["A"], "error": "old failure"}
    ranked.atomic(plan, {"cohorts": [cohort], "rows": [{"concept": "A", "mode": "dr"}], "error": "old failure"})
    manifest = {"status": "finalized", "ranked_queue_source": str(plan),
                "concepts": [{"name": "A", "slug": "a", "status": "done"}]}
    ranked.atomic(tmp_path / "research/test/manifest.json", manifest)
    queue = tmp_path / "concept-tree/RESEARCH_QUEUE.md"
    queue.parent.mkdir()
    queue.write_text("- [x] Concept: `A`\n")
    shared = SimpleNamespace(run_dir=lambda slug: tmp_path / "research" / slug,
                             run_lock=lambda slug: nullcontext(), load_manifest=lambda slug: manifest,
                             save_manifest=lambda value: None, write_draft=lambda value: None,
                             load_claims=lambda slug, errors: {"a": {"concept": "An editorial title bound with --as", "slug": "a"}},
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


def test_finalized_subset_defers_newly_eligible_concepts_without_completing_them(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMSX_HOME", str(tmp_path / "checkouts"))
    plan = tmp_path / "batch/plan.json"
    ranked.atomic(plan, {"cohorts": [{"id": "test", "parent": "Root", "status": "needs-review",
                                      "concepts": ["A", "B"]}],
                         "rows": [{"concept": name, "mode": "dr"} for name in ("A", "B")]})
    manifest = {"status": "finalized", "ranked_queue_source": str(plan),
                "concepts": [{"name": "A", "slug": "a", "status": "done"}]}
    ranked.atomic(tmp_path / "research/test/manifest.json", manifest)
    queue = tmp_path / "concept-tree/RESEARCH_QUEUE.md"
    queue.parent.mkdir()
    queue.write_text("- [ ] Concept: `A`\n- [ ] Concept: `B`\n")
    manifests = {"test": manifest}
    shared = SimpleNamespace(run_dir=lambda slug: tmp_path / "research" / slug,
                             run_lock=lambda slug: nullcontext(), load_manifest=lambda slug: manifests[slug],
                             save_manifest=lambda value: None, write_draft=lambda value: None,
                             load_claims=lambda slug, errors: {row["slug"]: {"concept": row["name"]}
                                                               for row in manifests[slug]["concepts"] if row["status"] == "done"},
                             slugify=str.lower,
                             RESEARCH_DIR=tmp_path / "research", locked=lambda path: nullcontext(),
                             atomic_write=lambda path, text: path.write_text(text))
    tree = SimpleNamespace(load_queue=lambda path: [{"concept": name, "done": False} for name in ("A", "B")],
                           load_nodes=lambda path: [{"concept": "A", "aliases": []}])
    def fake_load(name, path):
        if name == "ranked_adapter":
            return SimpleNamespace(load_shared=lambda: shared)
        return SimpleNamespace(runs=list) if name == "cohort_checkouts" else tree
    commands = []
    def fake_command(command, *args, **kwargs):
        commands.append(command)
        if command[1].endswith("codex_dr_run.py"):
            action, slug = command[2:4]
            if action == "init":
                slug = command[command.index("--slug") + 1]
            if action == "init" and slug not in manifests:
                manifests[slug] = {"status": "researching", "concepts": [{"name": "placeholder", "status": "pending"}]}
            elif action == "research":
                assert [row["name"] for row in manifests[slug]["concepts"]] == ["B"]
                for row in manifests[slug]["concepts"]:
                    row["status"] = "done"
            elif action == "gate":
                ranked.atomic(tmp_path / "research" / slug / "gate.json", {"verdicts": [{"verdict": "SUPPORTED"}]})
    monkeypatch.setattr(ranked, "load", fake_load)
    monkeypatch.setattr(ranked, "run_command", fake_command)
    assert ranked.execute_locked(tmp_path, tmp_path, plan, max_cohorts=1) == 0
    assert queue.read_text().splitlines() == ["- [x] Concept: `A`", "- [ ] Concept: `B`"]
    result = json.loads(plan.read_text())
    first, continuation = result["cohorts"]
    assert first["status"] == "complete" and first["concepts"] == ["A"]
    assert continuation["concepts"] == ["B"] and continuation["status"] == "pending"
    assert continuation["id"] != first["id"]
    successes = [json.loads(line) for line in (tmp_path / "checkouts/jobs/batches/batch/results.jsonl").read_text().splitlines()]
    assert [row["concept"] for row in successes] == ["A"]
    assert not any(command[2:3] == ["research"] for command in commands)
    assert ranked.execute_locked(tmp_path, tmp_path, plan, max_cohorts=1) == 0
    assert queue.read_text().splitlines() == ["- [x] Concept: `A`", "- [x] Concept: `B`"]
    assert [command[3] for command in commands if command[2:3] == ["research"]] == [continuation["id"]]


def test_finalized_manifest_without_validated_claims_cannot_complete_queue(tmp_path, monkeypatch):
    monkeypatch.setenv("LLMSX_HOME", str(tmp_path / "checkouts"))
    plan = tmp_path / "batch/plan.json"
    ranked.atomic(plan, {"cohorts": [{"id": "test", "parent": "Root", "status": "needs-review", "concepts": ["A"]}], "rows": []})
    manifest = {"status": "finalized", "ranked_queue_source": str(plan),
                "concepts": [{"name": "A", "slug": "a", "status": "done"}]}
    ranked.atomic(tmp_path / "research/test/manifest.json", manifest)
    shared = SimpleNamespace(run_dir=lambda slug: tmp_path / "research" / slug,
                             run_lock=lambda slug: nullcontext(), load_manifest=lambda slug: manifest,
                             save_manifest=lambda value: None, write_draft=lambda value: None,
                             load_claims=lambda slug, errors: {})
    monkeypatch.setattr(ranked, "eligible_now", lambda *args: ["A"])
    monkeypatch.setattr(ranked, "load", lambda *args: SimpleNamespace(load_shared=lambda: shared))
    monkeypatch.setattr(ranked, "run_command", lambda *args, **kwargs: None)
    assert ranked.execute_locked(tmp_path, tmp_path, plan) == 1
    assert "validated manifest claims" in json.loads(plan.read_text())["error"]


def test_custom_llmsx_home_reservation_is_visible_to_checkout_scanner(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
    monkeypatch.setenv("HUB_DIR", str(tmp_path))
    monkeypatch.setenv("LLMS_EXPLORER_REPO", str(tmp_path))
    monkeypatch.setenv("LLMSX_HOME", str(tmp_path / "custom"))
    checkouts = ranked.load("custom_home_checkouts", ROOT / "api/explorer_api/checkouts.py")
    plan = tmp_path / "batch/plan.json"
    ranked.atomic(plan, {"cohorts": [{"id": "test", "status": "pending", "concepts": ["A"]}], "rows": []})
    observed = []
    def broken(*args):
        observed.extend(checkouts._llmsx_batches())
        raise ImportError("stop after observing reservation")
    monkeypatch.setattr(ranked, "load", broken)
    assert ranked.execute_locked(tmp_path, tmp_path, plan) == 1
    assert observed[0]["pending"] == ["A"]
    assert (tmp_path / "custom/jobs/batches/batch/run.json").is_file()
    assert not (tmp_path / "home/.llmsx/jobs/batches/batch/run.json").exists()
