#!/usr/bin/env python3
"""Transfer paused suite reservations without changing research evidence or stage state.

The private ``handoffs.json`` receipt pins a source batch listing and a durable
target plan identity. Target progress may change, but its ``handoff_assignments``
mapping must remain immutable. No receipt means no transferred reservations.
Invalid receipts raise HandoffError; callers must keep reservations or refuse work.

Usage:
    python3 research_handoffs.py validate --source-run RUN
    python3 research_handoffs.py create --source-run RUN --target-plan PLAN
        --concept NAME --provenance TEXT
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = "research-handoff/v1"
FRESH_SECONDS = 600


class HandoffError(ValueError):
    """A receipt cannot safely release reservations or allow source work."""


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HandoffError(f"Cannot read {path}: {exc}") from exc


def _digest(value) -> str:
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _names(value, field: str) -> list[str]:
    if not isinstance(value, list) or not all(_text(name) for name in value):
        raise HandoffError(f"Invalid {field}: expected exact concept names")
    if len(value) != len(set(value)):
        raise HandoffError(f"Duplicate exact concepts in {field}")
    return value


def _source(source: Path) -> tuple[dict, list[dict], set[str]]:
    batches = _read(source / "batches.json")
    if not isinstance(batches, list) or not batches:
        raise HandoffError("Source batches.json must contain batches")
    names, ids = set(), set()
    for batch in batches:
        if not isinstance(batch, dict) or not _text(batch.get("id")):
            raise HandoffError("Invalid source batch")
        if (
            batch["id"] in ids
            or batch["id"] in (".", "..")
            or Path(batch["id"]).name != batch["id"]
        ):
            raise HandoffError("Source batch ids must be unique filesystem names")
        ids.add(batch["id"])
        concepts = _names(batch.get("concepts"), "source batch concepts")
        if names.intersection(concepts):
            raise HandoffError("A source concept occurs in multiple batches")
        names.update(concepts)
    identity = {"path": str(source), "name": source.name, "batches_sha256": _digest(batches)}
    return identity, batches, names


def _target(path: Path, selected: list[str], *, creating: bool = False) -> dict:
    plan = _read(path)
    if not isinstance(plan, dict) or not all(
        _text(plan.get(k)) for k in ("plan_id", "created", "domain")
    ):
        raise HandoffError("Target plan requires immutable plan_id, created and domain")
    assignments = plan.get("handoff_assignments")
    if (
        not isinstance(assignments, dict)
        or not assignments
        or not all(_text(name) and _text(cohort) for name, cohort in assignments.items())
    ):
        raise HandoffError("Target plan requires immutable handoff_assignments")
    rows, cohorts = plan.get("rows"), plan.get("cohorts")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise HandoffError("Target plan rows are malformed")
    if not isinstance(cohorts, list) or not all(isinstance(cohort, dict) for cohort in cohorts):
        raise HandoffError("Target plan cohorts are malformed")
    by_id = {}
    for cohort in cohorts:
        cid = cohort.get("id")
        if not _text(cid) or cid in by_id:
            raise HandoffError("Target cohort ids must be unique")
        _names(cohort.get("concepts"), "target cohort concepts")
        if "planned_concepts" in cohort:
            _names(cohort["planned_concepts"], "target cohort planned_concepts")
        by_id[cid] = cohort
    for name in selected:
        if sum(row.get("concept") == name for row in rows) != 1:
            raise HandoffError(f"Target needs exactly one accounted-for row for {name!r}")
        cohort = by_id.get(assignments.get(name))
        if cohort is None:
            raise HandoffError(f"Target original cohort is missing for {name!r}")
        original = cohort.get("planned_concepts", cohort["concepts"])
        if name not in original:
            raise HandoffError(f"Target original cohort no longer accounts for {name!r}")
        if creating and sum(name in c["concepts"] for c in cohorts) != 1:
            raise HandoffError(f"Target needs one current cohort assignment for {name!r}")
        if creating and name not in cohort["concepts"]:
            raise HandoffError(f"Target current assignment differs for {name!r}")
    return {
        "path": str(path),
        "plan_id": plan["plan_id"],
        "created": plan["created"],
        "domain": plan["domain"],
        "assignments_sha256": _digest(assignments),
    }


def _validate(source: Path, receipt) -> set[str]:
    identity, _, source_names = _source(source)
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        raise HandoffError("Invalid handoff schema")
    if receipt.get("source_run") != identity:
        raise HandoffError("Handoff source suite identity or batches changed")
    transfers = receipt.get("transfers")
    if not isinstance(transfers, list) or not transfers:
        raise HandoffError("Handoff receipt has no transfers")
    transferred, ids = set(), set()
    for entry in transfers:
        if not isinstance(entry, dict) or not all(
            _text(entry.get(k)) for k in ("id", "created", "provenance")
        ):
            raise HandoffError("Malformed handoff transfer")
        if entry["id"] in ids:
            raise HandoffError("Duplicate handoff transfer id")
        ids.add(entry["id"])
        try:
            stamp = datetime.fromisoformat(entry["created"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("missing timezone")
        except ValueError as exc:
            raise HandoffError("Invalid handoff creation date") from exc
        names = _names(entry.get("concepts"), "transfer concepts")
        if not names or not set(names).issubset(source_names) or transferred.intersection(names):
            raise HandoffError("Transfer concepts must be unique exact source concepts")
        target = entry.get("target_plan")
        if not isinstance(target, dict) or not _text(target.get("path")):
            raise HandoffError("Malformed target plan identity")
        path = Path(target["path"])
        if not path.is_absolute() or str(path.resolve()) != target["path"]:
            raise HandoffError("Target plan path must be absolute and canonical")
        if target != _target(path, names):
            raise HandoffError("Target plan identity or immutable assignments changed")
        transferred.update(names)
    return transferred


def validate_handoffs(source: Path) -> set[str]:
    """Return exact transferred names. A missing receipt transfers nothing."""
    source = Path(source).resolve()
    receipt = source / "handoffs.json"
    if not receipt.exists():
        return set()
    return _validate(source, _read(receipt))


def guard_handoff_batches(source: Path, batches: list[dict]) -> list[dict]:
    """Skip wholly transferred batches; refuse any cached mixed batch untouched."""
    transferred = validate_handoffs(source)
    originals = (
        {batch["id"]: batch for batch in _source(Path(source).resolve())[1]} if transferred else {}
    )
    keep = []
    for batch in batches:
        if transferred and (
            batch.get("id") not in originals
            or batch.get("concepts") != originals[batch["id"]]["concepts"]
        ):
            raise HandoffError(
                "Dispatch batch differs from source handoff identity; refuse cached mixed work"
            )
        names = set(_names(batch.get("concepts"), "dispatch concepts"))
        moved = names & transferred
        if moved and moved != names:
            raise HandoffError(
                f"Batch {batch.get('id')} has a partial handoff; refuse cached mixed work"
            )
        if not moved:
            keep.append(batch)
    return keep


@contextmanager
def suite_lock(source: Path):
    """Serialize new-suite dispatch and handoff writes using the same flock."""
    with (Path(source) / ".runner.lock").open("a", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise HandoffError("Source suite has an active runner or handoff lock") from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _assert_inactive(source: Path) -> None:
    for state in (source / "batches").glob("*/state.json"):
        if time.time() - state.stat().st_mtime < FRESH_SECONDS:
            raise HandoffError(f"Source suite has fresh state: {state}")
    # Older runners predate suite_lock. Inspect their exact run argument too.
    try:
        result = subprocess.run(
            ["ps", "ax", "-o", "pid=,args="], capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HandoffError("Cannot verify that source suite processes are inactive") from exc
    for line in result.stdout.splitlines():
        try:
            pid, command = line.strip().split(None, 1)
            args = shlex.split(command)
        except ValueError:
            continue
        is_suite = any(Path(arg).name == "research_suite.py" for arg in args)
        is_suite = is_suite or any(
            args[i : i + 2] == ["-m", "research_suite"] for i in range(len(args))
        )
        if int(pid) == os.getpid() or not is_suite:
            continue
        if "run" not in args:
            continue
        for i, arg in enumerate(args):
            value = (
                args[i + 1]
                if arg == "--run" and i + 1 < len(args)
                else arg.removeprefix("--run=")
                if arg.startswith("--run=")
                else None
            )
            if value in (source.name, str(source)):
                raise HandoffError(f"Source suite has a live runner process ({pid})")


def _atomic(path: Path, value) -> None:
    fd, name = tempfile.mkstemp(prefix=".handoffs-", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def create_handoff(
    source: Path, target_plan: Path, concepts: list[str], *, provenance: str
) -> dict:
    """Back up source control files and target plan, then atomically append a receipt.

    The caller must save a target plan first. This function never changes its
    plan, source batches, state, results or evidence. Only the receipt releases work.
    """
    source, target_plan = Path(source).resolve(), Path(target_plan).resolve()
    concepts = _names(concepts, "selected concepts")
    if not concepts or not _text(provenance):
        raise HandoffError("Select concepts and provide handoff provenance")
    with suite_lock(source):
        _assert_inactive(source)
        identity, batches, names = _source(source)
        previous = validate_handoffs(source)
        if not set(concepts).issubset(names) or previous.intersection(concepts):
            raise HandoffError("Select untransferred exact source concepts")
        for batch in batches:
            if not set(batch["concepts"]).intersection(concepts):
                continue
            state_path = source / "batches" / batch["id"] / "state.json"
            if state_path.exists():
                state = _read(state_path)
                if not isinstance(state, dict) or not isinstance(state.get("stages", {}), dict):
                    raise HandoffError("Source batch state is malformed")
                register = state.get("stages", {}).get("register", {})
                if not isinstance(register, dict) or register.get("status") == "done":
                    raise HandoffError("Cannot transfer an already registered source batch")
        target = _target(target_plan, concepts, creating=True)
        path = source / "handoffs.json"
        receipt = (
            _read(path)
            if path.exists()
            else {"schema": SCHEMA, "source_run": identity, "transfers": []}
        )
        stamp = datetime.now(UTC).isoformat()
        entry = {
            "id": str(uuid.uuid4()),
            "created": stamp,
            "provenance": provenance,
            "target_plan": target,
            "concepts": concepts,
        }
        receipt["transfers"].append(entry)
        _validate(source, receipt)
        backup = source / "backups" / f"handoff-{datetime.now(UTC):%Y%m%dT%H%M%S}-{entry['id']}"
        backup.mkdir(parents=True, mode=0o700)
        controls = [
            source / name for name in ("batches.json", "scope.json", "run.json", "handoffs.json")
        ]
        controls.extend((source / "batches").glob("*/state.json"))
        for control in controls:
            if control.exists():
                saved = backup / control.relative_to(source)
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(control, saved)
        shutil.copy2(target_plan, backup / "target-plan.json")
        # Recheck after backup I/O. A concurrent old runner or edited target
        # must never produce a receipt that looks committed but has no owner.
        _assert_inactive(source)
        _validate(source, receipt)
        _atomic(path, receipt)
        return {"receipt": str(path), "backup": str(backup), "transfer": entry}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "create"):
        command = sub.add_parser(name)
        command.add_argument("--source-run", type=Path, required=True)
        if name == "create":
            command.add_argument("--target-plan", type=Path, required=True)
            command.add_argument("--concept", action="append", required=True)
            command.add_argument("--provenance", required=True)
    args = parser.parse_args()
    try:
        result = (
            {"transferred": sorted(validate_handoffs(args.source_run))}
            if args.command == "validate"
            else create_handoff(
                args.source_run, args.target_plan, args.concept, provenance=args.provenance
            )
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (HandoffError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
