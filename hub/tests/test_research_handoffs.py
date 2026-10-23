"""Private suite handoffs release exact concepts only with durable ownership proof."""

import argparse
import fcntl
import importlib.util
import json
import os
import types
from pathlib import Path

import pytest

import research_handoffs as rh
import research_suite as rs

REPO = Path(__file__).resolve().parents[2]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def handoff(tmp_path, monkeypatch):
    hub = tmp_path / "hub"
    source = hub / "research/.pipeline/paused-suite"
    batches = [
        {"id": "mixed", "concepts": ["Atlas A", "Atlas B"]},
        {"id": "single", "concepts": ["Atlas C"]},
    ]
    write(source / "batches.json", batches)
    write(source / "run.json", {"started": "2026-10-14T00:00:00Z", "args": {"run": source.name}})
    write(source / "scope.json", {"concepts": ["Atlas A", "Atlas B", "Atlas C"]})
    for batch in batches:
        state = source / "batches" / batch["id"] / "state.json"
        write(
            state,
            {
                "stages": {
                    name: {"status": "done"}
                    for name in ("discover", "snapshot", "extract", "synth", "validate")
                }
            },
        )
        os.utime(state, (1, 1))
    evidence = source / "batches/mixed/snapshots/evidence.txt"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("Existing source snapshots remain reusable.")
    target = tmp_path / "new-run/plan.json"
    write(
        target,
        {
            "plan_id": "independent-plan-123",
            "created": "2026-10-22T00:00:00Z",
            "domain": "mongodb",
            "status": "planned",
            "rows": [
                {"concept": name, "status": "pending"} for name in ("Atlas A", "Atlas B", "Atlas C")
            ],
            "cohorts": [
                {"id": "cohort-1", "concepts": ["Atlas A", "Atlas B"]},
                {"id": "cohort-2", "concepts": ["Atlas C"]},
            ],
            "handoff_assignments": {
                "Atlas A": "cohort-1",
                "Atlas B": "cohort-1",
                "Atlas C": "cohort-2",
            },
        },
    )
    monkeypatch.setattr(rh.subprocess, "run", lambda *a, **k: types.SimpleNamespace(stdout=""))
    monkeypatch.setenv("HUB_DIR", str(hub))
    monkeypatch.setenv("LLMSX_HOME", str(tmp_path / "llmsx"))
    monkeypatch.setattr(rs, "HUB", hub)
    spec = importlib.util.spec_from_file_location(
        "standalone_checkouts", REPO / "api/explorer_api/checkouts.py"
    )
    checkouts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checkouts)
    return source, target, batches, checkouts


def transfer(handoff, names=("Atlas A",)):
    source, target, _, _ = handoff
    return rh.create_handoff(
        source, target, list(names), provenance="TASK-832 explicit paused-suite transfer"
    )


def test_subset_transfer_releases_only_exact_names_and_backs_up_unchanged_evidence(handoff):
    source, target, batches, checkouts = handoff
    before = {
        path.relative_to(source): path.read_bytes() for path in source.rglob("*") if path.is_file()
    }
    assert checkouts.held_by("Atlas A") == "the research suite run paused-suite"
    result = transfer(handoff)
    assert rh.validate_handoffs(source) == {"Atlas A"}
    assert checkouts.held_by("atlas a") is None
    assert checkouts.held_by("Atlas B") == "the research suite run paused-suite"
    assert checkouts.held_by("Atlas C") == "the research suite run paused-suite"
    assert load(source / "batches.json") == batches
    for relative, content in before.items():
        assert (source / relative).read_bytes() == content
    backup = Path(result["backup"])
    assert load(backup / "target-plan.json") == load(target)
    assert load(backup / "batches.json") == batches
    assert (backup / "batches/mixed/state.json").read_bytes() == before[
        Path("batches/mixed/state.json")
    ]
    assert (source / "handoffs.json").stat().st_mode & 0o077 == 0
    assert "register" not in load(source / "batches/mixed/state.json")["stages"]


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "malformed",
        "different-id",
        "created",
        "domain",
        "assignments",
        "missing-row",
        "duplicate-row",
        "missing-cohort",
        "removed-membership",
    ],
)
def test_missing_malformed_or_changed_target_plan_keeps_reservation_even_after_cached_release(
    handoff, change
):
    source, target, _, checkouts = handoff
    transfer(handoff)
    assert checkouts.held_by("Atlas A") is None
    plan = load(target)
    if change == "missing":
        target.unlink()
    elif change == "malformed":
        target.write_text("{")
    else:
        if change == "different-id":
            plan["plan_id"] = "same-names-unrelated-plan"
        elif change == "created":
            plan["created"] = "different-run"
        elif change == "domain":
            plan["domain"] = "other-domain"
        elif change == "assignments":
            plan["handoff_assignments"]["Atlas A"] = "cohort-2"
        elif change == "missing-row":
            plan["rows"] = plan["rows"][1:]
        elif change == "duplicate-row":
            plan["rows"].append(plan["rows"][0])
        elif change == "missing-cohort":
            plan["cohorts"] = plan["cohorts"][1:]
        elif change == "removed-membership":
            plan["cohorts"][0]["concepts"] = ["Atlas B"]
        write(target, plan)
    with pytest.raises(rh.HandoffError):
        rh.validate_handoffs(source)
    assert checkouts.held_by("Atlas A") == "the research suite run paused-suite"
    with pytest.raises(rh.HandoffError):
        rh.guard_handoff_batches(source, load(source / "batches.json"))


def test_progress_status_and_safe_continuation_keep_original_handoff_valid(handoff):
    source, target, _, checkouts = handoff
    transfer(handoff)
    plan = load(target)
    plan["status"] = "running"
    plan["rows"][0]["status"] = "complete"
    plan["cohorts"][0].update(
        planned_concepts=["Atlas A", "Atlas B"], concepts=["Atlas B"], status="complete"
    )
    plan["cohorts"].append(
        {"id": "continuation", "concepts": ["Atlas A"], "continuation_of": "cohort-1"}
    )
    write(target, plan)
    assert rh.validate_handoffs(source) == {"Atlas A"}
    assert checkouts.held_by("Atlas A") is None


@pytest.mark.parametrize(
    "change",
    ["torn", "wrong-schema", "source-path", "source-batches", "wrong-name", "empty", "date"],
)
def test_invalid_receipts_keep_all_source_reservations(handoff, change):
    source, _, _, checkouts = handoff
    transfer(handoff)
    path = source / "handoffs.json"
    receipt = load(path)
    if change == "torn":
        path.write_text('{"schema":')
    else:
        if change == "wrong-schema":
            receipt["schema"] = "research-handoff/v0"
        elif change == "source-path":
            receipt["source_run"]["path"] += "-unrelated"
        elif change == "source-batches":
            batches = load(source / "batches.json")
            batches[0]["concepts"].append("Atlas Extra")
            write(source / "batches.json", batches)
        elif change == "wrong-name":
            receipt["transfers"][0]["concepts"] = ["atlas a"]
        elif change == "empty":
            receipt["transfers"] = []
        elif change == "date":
            receipt["transfers"][0]["created"] = "yesterday"
        write(path, receipt)
    assert checkouts.held_by("Atlas A") == "the research suite run paused-suite"
    with pytest.raises(rh.HandoffError):
        rh.validate_handoffs(source)


def test_removed_receipt_immediately_restores_cached_reservation(handoff):
    source, _, _, checkouts = handoff
    transfer(handoff)
    assert checkouts.held_by("Atlas A") is None
    (source / "handoffs.json").unlink()
    assert checkouts.held_by("Atlas A") == "the research suite run paused-suite"


def test_interrupted_receipt_write_releases_nothing_and_keeps_backups(handoff, monkeypatch):
    source, _, _, checkouts = handoff

    def fail_replace(self, destination):
        raise OSError("simulated interrupted receipt rename")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="interrupted"):
        transfer(handoff)
    assert not (source / "handoffs.json").exists()
    assert list((source / "backups").glob("handoff-*/batches.json"))
    assert not list(source.glob(".handoffs-*.tmp"))
    assert rh.validate_handoffs(source) == set()
    assert checkouts.held_by("Atlas A") == "the research suite run paused-suite"


@pytest.mark.parametrize("active", ["fresh-state", "locked", "legacy-process", "module-process"])
def test_create_refuses_active_source_suite(handoff, monkeypatch, active):
    source, _, _, _ = handoff
    lock = None
    if active == "fresh-state":
        os.utime(source / "batches/mixed/state.json", None)
    elif active == "locked":
        lock = (source / ".runner.lock").open("a")
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    else:
        script = (
            "-m research_suite" if active == "module-process" else "/old/scripts/research_suite.py"
        )
        monkeypatch.setattr(
            rh.subprocess,
            "run",
            lambda *a, **k: types.SimpleNamespace(
                stdout=f"123 /usr/bin/python {script} run --run paused-suite\n"
            ),
        )
    try:
        with pytest.raises(rh.HandoffError, match="fresh state|active runner|live runner"):
            transfer(handoff)
    finally:
        if lock:
            lock.close()
    assert not (source / "handoffs.json").exists()


@pytest.mark.parametrize(
    "invalid", ["unassigned", "duplicate-cohort", "wrong-exact-name", "registered"]
)
def test_create_refuses_unaccounted_target_or_completed_source(handoff, invalid):
    source, target, _, _ = handoff
    plan = load(target)
    names = ["Atlas A"]
    if invalid == "unassigned":
        plan["cohorts"][0]["concepts"] = ["Atlas B"]
    elif invalid == "duplicate-cohort":
        plan["cohorts"][1]["concepts"].append("Atlas A")
    elif invalid == "wrong-exact-name":
        names = ["atlas a"]
    else:
        state = source / "batches/mixed/state.json"
        write(state, {"stages": {"register": {"status": "done"}}})
        os.utime(state, (1, 1))
    write(target, plan)
    with pytest.raises(rh.HandoffError):
        rh.create_handoff(source, target, names, provenance="explicit transfer")
    assert not (source / "handoffs.json").exists()


def test_multiple_subset_receipts_back_up_previous_ownership(handoff):
    source, _, _, _ = handoff
    transfer(handoff)
    second = transfer(handoff, ("Atlas C",))
    assert rh.validate_handoffs(source) == {"Atlas A", "Atlas C"}
    previous = load(Path(second["backup"]) / "handoffs.json")
    assert previous["transfers"][0]["concepts"] == ["Atlas A"]
    with pytest.raises(rh.HandoffError, match="untransferred"):
        transfer(handoff)


def test_old_suite_refuses_partial_cached_batch_before_dispatch_or_metadata_write(
    handoff, monkeypatch
):
    source, _, batches, _ = handoff
    transfer(handoff)
    state_before = (source / "batches/mixed/state.json").read_bytes()
    meta_before = (source / "run.json").read_bytes()
    monkeypatch.setattr(rs, "load_hub_modules", lambda: pytest.fail("must refuse before hub load"))
    with pytest.raises(rh.HandoffError, match="partial handoff"):
        rs.run_pipeline(source, batches, argparse.Namespace(), Path("."))
    with pytest.raises(rh.HandoffError, match="partial handoff"):
        rs.stage_register(source, batches[0], Path("."))
    args = argparse.Namespace(run=source.name, only=None, pilot=0, pilot_pick=None)
    assert rs.cmd_run(args) == 4
    assert (source / "run.json").read_bytes() == meta_before
    assert (source / "batches/mixed/state.json").read_bytes() == state_before
    assert not (source / "results.jsonl").exists()


def test_old_suite_skips_wholly_transferred_batches_without_marking_done(handoff, monkeypatch):
    source, _, batches, _ = handoff
    transfer(handoff, ("Atlas A", "Atlas B", "Atlas C"))
    assert rh.guard_handoff_batches(source, batches) == []
    monkeypatch.setattr(rs, "load_hub_modules", lambda: pytest.fail("no work remains"))
    assert rs.run_pipeline(source, batches, argparse.Namespace(), Path(".")) == 0
    assert rs.cmd_run(argparse.Namespace(run=source.name, only=None, pilot=0, pilot_pick=None)) == 0
    assert rs.stage_register(source, batches[0], Path(".")) is None
    assert "register" not in load(source / "batches/mixed/state.json")["stages"]
    assert not (source / "results.jsonl").exists()


def test_guard_preserves_untransferred_batch(handoff):
    source, _, batches, _ = handoff
    transfer(handoff, ("Atlas A", "Atlas B"))
    assert rh.guard_handoff_batches(source, batches) == [batches[1]]


def test_narrowed_dispatch_cannot_run_a_cached_mixed_batch(handoff):
    source, _, batches, _ = handoff
    transfer(handoff)
    narrowed = {**batches[0], "concepts": ["Atlas B"]}
    with pytest.raises(rh.HandoffError, match="differs from source"):
        rh.guard_handoff_batches(source, [narrowed])
    with pytest.raises(rh.HandoffError, match="differs from source"):
        rs.stage_register(source, narrowed, Path("."))


def test_interrupted_append_preserves_previous_receipt(handoff, monkeypatch):
    source, _, _, checkouts = handoff
    transfer(handoff)
    before = (source / "handoffs.json").read_bytes()

    def fail_replace(self, destination):
        raise OSError("interrupted append")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="interrupted append"):
        transfer(handoff, ("Atlas C",))
    assert (source / "handoffs.json").read_bytes() == before
    assert rh.validate_handoffs(source) == {"Atlas A"}
    assert checkouts.held_by("Atlas C") == "the research suite run paused-suite"
