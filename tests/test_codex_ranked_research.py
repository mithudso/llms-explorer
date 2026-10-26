"""Ranked automation preserves queue identity and resumes without model calls."""
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ranked", ROOT / "scripts/codex_ranked_research.py")
ranked = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ranked)


def test_ranked_parser_keeps_literal_pipes_and_parent():
    rows = ranked.ranked_rows("| 1 | 4.2 | RESEARCH | A | B | Parent | dr | pending |")
    assert rows[0]["concept"] == "A|B"
    assert rows[0]["parent"] == "Parent"


def test_new_ranked_plan_uses_sol_medium(tmp_path, monkeypatch):
    source = tmp_path / "ranked.md"
    source.write_text("| 1 | 4.2 | RESEARCH | New concept | Parent | dr | pending |\n")
    tree = SimpleNamespace(load_nodes=lambda path: [], load_queue=lambda path: [
        {"concept": "New concept", "done": False}])
    checkouts = SimpleNamespace(_scan=lambda: (None, {}))
    monkeypatch.setattr(ranked, "load", lambda name, path: checkouts if name == "ranked_checkouts" else tree)
    monkeypatch.setattr(ranked, "queue_parser", lambda repo: None)
    plan = ranked.make_plan(tmp_path, tmp_path, source)
    assert (plan["model"], plan["effort"]) == ("gpt-6.1-sol", "medium")
    assert plan["cohorts"][0]["concepts"] == ["New concept"]


@pytest.mark.parametrize('signum', [signal.SIGINT, signal.SIGTERM])
def test_cancelling_ranked_parent_stops_phase_and_isolated_worker(tmp_path, signum):
    ready = tmp_path / 'ready.json'
    phase = tmp_path / 'phase.py'
    phase.write_text('''import json, os, signal, subprocess, sys, time
from pathlib import Path
worker = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], start_new_session=True)
def stop(signum, frame):
    worker.kill()
    worker.wait()
    raise SystemExit(128 + signum)
signal.signal(signal.SIGTERM, stop)
ready = Path(sys.argv[1])
temporary = ready.with_suffix('.tmp')
temporary.write_text(json.dumps({'phase': os.getpid(), 'worker': worker.pid}))
temporary.replace(ready)
time.sleep(30)
''')
    runner = tmp_path / 'runner.py'
    runner.write_text(f'''import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('ranked_cancel', {str(ROOT / 'scripts/codex_ranked_research.py')!r})
ranked = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ranked)
ranked.run_command([sys.executable, {str(phase)!r}, {str(ready)!r}], Path({str(tmp_path / 'phase.log')!r}), os.environ, timeout=30)
''')
    parent = subprocess.Popen([sys.executable, str(runner)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    children = {}
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert ready.exists(), 'phase failed to start'
        children = json.loads(ready.read_text())
        parent.send_signal(signum)
        parent.communicate(timeout=5)
        assert parent.returncode == 128 + signum
        for pid in children.values():
            with pytest.raises(ProcessLookupError):
                os.kill(pid, 0)
        assert json.loads((tmp_path / 'phase.log').read_text())['cancelled']
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.communicate()
        for pid in children.values():
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


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


def test_queue_completion_updates_both_roots_without_adding_private_names(tmp_path):
    hub, repo = tmp_path / "hub", tmp_path / "repo"
    for root in (hub, repo):
        (root / "concept-tree").mkdir(parents=True)
        (root / "concept-tree/RESEARCH_QUEUE.md").write_text('- [ ] Concept: `Public`\n')
    queue = hub / "concept-tree/RESEARCH_QUEUE.md"
    queue.write_text(queue.read_text() + '- [ ] Concept: `Private`\n')
    shared = SimpleNamespace(RESEARCH_DIR=tmp_path / "research", locked=lambda path: nullcontext(),
                             atomic_write=lambda path, text: path.write_text(text))
    ranked.complete_queue(shared, hub, ["Public", "Private"], repo)
    assert '[x]' in queue.read_text()
    assert (repo / "concept-tree/RESEARCH_QUEUE.md").read_text() == '- [x] Concept: `Public`\n'


def test_queue_completion_preserves_literal_inline_code_and_other_rows(tmp_path):
    queue = tmp_path / 'concept-tree/RESEARCH_QUEUE.md'
    queue.parent.mkdir()
    queue.write_text('- [ ] Concept: ``The `$in` operator`` | Parent: `Root`\n'
                     '- [ ] Concept: `Another concept` | Parent: `Root`\n')
    shared = SimpleNamespace(RESEARCH_DIR=tmp_path / 'research', locked=lambda path: nullcontext(),
                             atomic_write=lambda path, text: path.write_text(text))
    ranked.complete_queue(shared, tmp_path, ['The `$in` operator'])
    assert queue.read_text().splitlines() == ['- [x] Concept: ``The `$in` operator`` | Parent: `Root`',
                                             '- [ ] Concept: `Another concept` | Parent: `Root`']


def test_new_revisit_gets_a_fresh_identity():
    names = ["Previously researched"]
    assert ranked.cohort_id(names) == ranked.cohort_id(names)
    assert ranked.cohort_id(names, revisit=True) != ranked.cohort_id(names, revisit=True)


def test_continue_on_review_processes_other_cohorts_without_retrying_dissent(tmp_path, monkeypatch):
    plan = tmp_path / 'plan.json'
    ranked.atomic(plan, {'continue_on_review': True, 'cohorts': [
        {'id': 'a', 'status': 'pending'}, {'id': 'b', 'status': 'pending'}]})
    calls = []
    def execute(repo, hub, path):
        value = json.loads(path.read_text())
        pending = next(row for row in value['cohorts'] if row['status'] == 'pending')
        calls.append(pending['id'])
        pending['status'] = 'needs-review' if pending['id'] == 'a' else 'complete'
        ranked.atomic(path, value)
        return 1 if pending['id'] == 'a' else 0
    monkeypatch.setattr(ranked, 'execute_locked', execute)
    assert ranked.execute_all(tmp_path, tmp_path, plan) == 0
    assert calls == ['a', 'b']
    assert json.loads(plan.read_text())['cohorts'][0]['status'] == 'needs-review'


def test_continue_on_review_stops_on_setup_failure_without_advancing(tmp_path, monkeypatch):
    plan = tmp_path / 'plan.json'
    ranked.atomic(plan, {'continue_on_review': True, 'cohorts': [{'id': 'a', 'status': 'pending'}]})
    calls = []
    def execute(*args):
        calls.append(1)
        return 1
    monkeypatch.setattr(ranked, 'execute_locked', execute)
    assert ranked.execute_all(tmp_path, tmp_path, plan) == 1
    assert len(calls) == 1


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
    tree = SimpleNamespace(load_queue=lambda path: [{"concept": name, "done": False, "line": index}
                                                   for index, name in enumerate(("A", "B"), 1)],
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


@pytest.mark.parametrize('cancel', [SystemExit(143), KeyboardInterrupt()])
@pytest.mark.parametrize('stage', ['setup', 'phase'])
def test_cancellation_releases_batch_marker_without_completing_pending_concepts(tmp_path, monkeypatch, cancel, stage):
    monkeypatch.setenv('LLMSX_HOME', str(tmp_path / 'checkouts'))
    monkeypatch.setenv('HUB_DIR', str(tmp_path))
    monkeypatch.setenv('LLMS_EXPLORER_REPO', str(tmp_path))
    checkouts = ranked.load('cancelled_batch_checkouts', ROOT / 'api/explorer_api/checkouts.py')
    plan = tmp_path / 'batch/plan.json'
    ranked.atomic(plan, {'cohorts': [{'id': 'test', 'parent': 'Root', 'status': 'pending', 'concepts': ['A']}], 'rows': []})
    def cancelled(*args, **kwargs):
        raise cancel
    if stage == 'setup':
        monkeypatch.setattr(ranked, 'load', cancelled)
    else:
        shared = SimpleNamespace(run_dir=lambda slug: tmp_path / 'research' / slug)
        monkeypatch.setattr(ranked, 'load', lambda *args: SimpleNamespace(load_shared=lambda: shared))
        monkeypatch.setattr(ranked, 'eligible_now', lambda *args: ['A'])
        monkeypatch.setattr(ranked, 'run_command', cancelled)
    with pytest.raises(type(cancel)) as caught:
        ranked.execute_locked(tmp_path, tmp_path, plan)
    assert caught.value is cancel
    marker = json.loads((tmp_path / 'checkouts/jobs/batches/batch/run.json').read_text())
    assert marker['status'] == 'cancelled' and marker['concepts'] == []
    saved = json.loads(plan.read_text())
    assert saved['status'] == 'cancelled'
    assert saved['cohorts'][0]['status'] == ('pending' if stage == 'setup' else 'cancelled')
    assert checkouts._llmsx_batches() == []
