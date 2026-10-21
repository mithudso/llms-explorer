#!/usr/bin/env python3
"""Plan and resume ranked /dr research in source-sharing cohorts.

Only `run` starts model calls. Plans preserve every ranked row, skip existing
checkouts, and group eligible concepts by parent. Each cohort uses Luna/max,
the shared source library, a blind Sol/medium gate, and website completion.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def key(name):
    return " ".join(name.split()).casefold()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def ranked_rows(text):
    rows = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        try:
            score = float(cells[1])
        except ValueError:
            continue
        rows.append({"rank": int(cells[0]), "cvs": score, "decision": cells[2],
                     "concept": "|".join(cells[3:-3]), "parent": cells[-3],
                     "mode": cells[-2], "ranked_state": cells[-1]})
    return rows


def make_plan(repo, hub, source, size=4):
    ct = load("ranked_concept_tree", hub / "scripts/concept_tree.py")
    checkouts = load("ranked_checkouts", repo / "api/explorer_api/checkouts.py")
    _, held = checkouts._scan()
    nodes = ct.load_nodes(hub / "concept-tree/tree.json")
    names = {key(node["concept"]) for node in nodes}
    aliases = {key(alias) for node in nodes for alias in node.get("aliases", [])}
    pending = {key(row["concept"]) for row in ct.load_queue(hub / "concept-tree/RESEARCH_QUEUE.md") if not row["done"]}
    text = source.read_text()
    rows, groups = ranked_rows(text), defaultdict(list)
    seen = set()
    for row in rows:
        name = key(row["concept"])
        if name in seen:
            row["status"] = "duplicate"
        elif row["cvs"] < 3.2 or row["decision"] not in ("RESEARCH", "—"):
            row["status"] = "below-gate"
        elif name not in pending:
            row["status"] = "no-longer-pending"
        elif name in held:
            row.update(status="checked-out", holder=held[name])
        elif name in aliases and row["mode"] != "revisit":
            row["status"] = "alias-covered"
        elif name in names and row["mode"] != "revisit":
            row["status"] = "already-researched"
        else:
            row["status"] = "pending"
            groups[row["parent"]].append(row)
        seen.add(name)
    cohorts = []
    for parent, items in groups.items():
        items.sort(key=lambda row: (row["rank"], -row["cvs"]))
        for start in range(0, len(items), size):
            batch = items[start:start + size]
            digest = hashlib.sha256(json.dumps([row["concept"] for row in batch]).encode()).hexdigest()[:8]
            cohorts.append({"id": f"ranked-{digest}", "parent": parent,
                            "concepts": [row["concept"] for row in batch],
                            "priority": min(row["rank"] for row in batch), "status": "pending",
                            "source_strategy": "Shared parent evidence, source-library FTS and cached snapshots; child-specific claims."})
    cohorts.sort(key=lambda cohort: cohort["priority"])
    return {"created": datetime.now(UTC).isoformat(), "source": str(source),
            "source_sha256": hashlib.sha256(text.encode()).hexdigest(), "model": "gpt-6-luna",
            "effort": "max", "rows": rows, "cohorts": cohorts, "status": "planned"}


def run_command(command, log, env, timeout=7200):
    started = time.monotonic()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                               env=env, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        with log.open("a") as stream:
            stream.write(json.dumps({"command": command, "timed_out": True, "stdout": stdout, "stderr": stderr}) + "\n")
        raise RuntimeError("Cohort phase exceeded its remaining time budget") from None
    with log.open("a") as stream:
        stream.write(json.dumps({"command": command, "seconds": round(time.monotonic() - started, 2),
                                 "returncode": process.returncode, "stdout": stdout, "stderr": stderr}) + "\n")
    if process.returncode:
        raise RuntimeError(f"{command[2] if len(command)>2 else command[0]} failed: {(stderr or stdout)[-1500:]}")
    return stdout


def prepare_manifest(shared, slug, parent, names, plan_path):
    """Preserve punctuation in names; the native init flag uses comma splitting."""
    with shared.run_lock(slug):
        manifest = shared.load_manifest(slug)
        if not manifest.get("ranked_queue_source"):
            if any(row["status"] != "pending" for row in manifest["concepts"]):
                raise ValueError("Cannot change an existing researched run's concept list")
            seen, concepts = set(), []
            for name in names:
                concept_slug = shared.slugify(name)
                if concept_slug in seen:
                    concept_slug += "-" + hashlib.sha256(name.encode()).hexdigest()[:6]
                seen.add(concept_slug)
                concepts.append({"name": name, "slug": concept_slug, "status": "pending"})
            manifest["concepts"] = concepts
        manifest.update(cohort_parent=parent, ranked_queue_source=str(plan_path), budget_minutes=45)
        shared.save_manifest(manifest)
        shared.write_draft(manifest)
    return manifest


def complete_queue(shared, hub, names):
    queue = hub / "concept-tree/RESEARCH_QUEUE.md"
    with shared.locked(shared.RESEARCH_DIR / ".global.lock"):
        text = queue.read_text()
        for name in names:
            pattern = re.compile(r"^(\s*-\s*)\[ \](\s*Concept:\s*`" + re.escape(name) + r"`[^\n]*)$", re.MULTILINE)
            text = pattern.sub(lambda match: match[1] + "[x]" + match[2], text)
        shared.atomic_write(queue, text)


def eligible_now(repo, hub, cohort, run_id):
    checkouts = load("cohort_checkouts", repo / "api/explorer_api/checkouts.py")
    # The batch and its own /dr manifest are resumable holders of this work.
    own = {run_id, cohort["id"]}
    held = {key(name) for run in checkouts.runs() if run["name"] not in own for name in run["pending"]}
    ct = load("cohort_tree", hub / "scripts/concept_tree.py")
    pending = {key(row["concept"]) for row in ct.load_queue(hub / "concept-tree/RESEARCH_QUEUE.md") if not row["done"]}
    nodes = ct.load_nodes(hub / "concept-tree/tree.json")
    covered = {key(name) for node in nodes for name in [node["concept"], *node.get("aliases", [])]}
    revisit = {key(row["concept"]) for row in cohort.get("rows", []) if row.get("mode") == "revisit"}
    return [name for name in cohort["concepts"] if key(name) not in held and key(name) in pending
            and (key(name) not in covered or key(name) in revisit)]


def execute(repo, hub, plan_path, max_cohorts=None):
    with (plan_path.parent / ".runner.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("This ranked plan already has a runner") from None
        return execute_locked(repo, hub, plan_path, max_cohorts)


def execute_locked(repo, hub, plan_path, max_cohorts=None):
    plan = json.loads(plan_path.read_text())
    run_id = plan_path.parent.name
    marker = Path.home() / ".llmsx/jobs/batches" / run_id / "run.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    atomic(marker, {"root": run_id, "status": "in-progress",
                    "concepts": [name for cohort in plan["cohorts"] if cohort["status"] != "complete" for name in cohort["concepts"]]})
    plan.update(status="running", pid=os.getpid(), started=datetime.now(UTC).isoformat())
    atomic(plan_path, plan)
    adapter = [sys.executable, str(repo / "scripts/codex_dr_run.py")]
    env = {**os.environ, "HUB_DIR": str(hub), "LLMS_EXPLORER_REPO": str(repo)}
    os.environ.update(HUB_DIR=str(hub), LLMS_EXPLORER_REPO=str(repo))
    shared = load("ranked_adapter", repo / "scripts/codex_dr_run.py").load_shared()
    completed = 0
    try:
        for cohort in plan["cohorts"]:
            if cohort["status"] == "complete":
                continue
            cohort["rows"] = [row for row in plan["rows"] if row["concept"] in cohort["concepts"]]
            if (plan_path.parent / "STOP").exists() or (max_cohorts is not None and completed >= max_cohorts):
                break
            # Recheck other holders immediately before dispatch. The local batch
            # marker reserves this plan, so ignore only this plan's own label.
            picked = eligible_now(repo, hub, cohort, run_id)
            if not picked:
                cohort.update(status="skipped", note="No eligible concepts remain after checking coverage and other holders.")
                atomic(plan_path, plan)
                continue
            cohort.update(status="running", started=datetime.now(UTC).isoformat())
            atomic(plan_path, plan)
            slug = cohort["id"]
            log = plan_path.parent / f"{slug}.events.jsonl"
            parent = cohort["parent"] if cohort["parent"] != "—" else "Ranked concept research"
            deadline = time.monotonic() + 45 * 60
            def phase(command, limit=2700, deadline=deadline, log=log):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("Cohort time budget exhausted at phase boundary")
                return run_command(command, log, env, timeout=min(limit, remaining))
            phase(adapter + ["init", parent, "--slug", slug, "--concepts", "cohort initialization"])
            manifest = prepare_manifest(shared, slug, parent, picked, plan_path)
            # Include pages saved by earlier /dr runs in the shared FTS index.
            phase([sys.executable, str(hub / "scripts/source_library.py"), "reconcile"], 300)
            if manifest["status"] != "finalized":
                phase(adapter + ["research", slug, "--max-parallel", "4"])
                manifest = shared.load_manifest(slug)
                errors = []
                shared.load_claims(slug, errors)
                if errors or any(concept["status"] != "done" for concept in manifest["concepts"]):
                    raise RuntimeError(f"cohort has blocked or invalid claims: {errors}")
                output = repo / ".agents/skills" / slug / "SKILL.md"
                phase(adapter + ["render", slug, "--kind", "standalone", "--out", str(output),
                                      "--description", f"Explain {parent} through source-anchored concept research. TRIGGER: {parent}. SKIP: unrelated topics.",
                                      "--keywords", "research,concepts,reference,sources,mechanism,limits,operations,validation"])
                phase(adapter + ["gate", slug, "--model", "gpt-6.1-sol", "--effort", "medium"], 1200)
                gate = json.loads((shared.run_dir(slug) / "gate.json").read_text())
                if not gate.get("verdicts"):
                    raise RuntimeError("Blind claim gate returned no verdicts")
                dissent = [row for row in gate["verdicts"] if row.get("verdict") != "SUPPORTED"]
                if dissent:
                    raise RuntimeError(f"blind claim gate needs review: {len(dissent)} non-supported verdicts")
                phase(adapter + ["finish", slug, "--status", "COMPLETED", "--stop-reason", "Ranked source-sharing cohort; scout and blind gate completed."])
            # A completed run with a failed website write can resume without
            # repeating paid research. This also checks all four website surfaces.
            run_command([sys.executable, str(repo / "scripts/research_site_sync.py"), "--repo", str(repo),
                         "--hub", str(hub), "--apply"], log, env, timeout=600)
            complete_queue(shared, hub, picked)
            for name in picked:
                with (marker.parent / "results.jsonl").open("a") as stream:
                    stream.write(json.dumps({"concept": name, "status": "complete", "run": slug}) + "\n")
            cohort.update(status="complete", finished=datetime.now(UTC).isoformat(), run=str(shared.run_dir(slug)))
            completed += 1
            atomic(plan_path, plan)
            print(json.dumps({"cohort": slug, "status": "complete", "concepts": picked}), flush=True)
        plan["status"] = "complete" if all(cohort["status"] in ("complete", "skipped") for cohort in plan["cohorts"]) else "stopped"
        atomic(plan_path, plan)
        atomic(marker, {"root": run_id, "status": plan["status"], "concepts": []})
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        cohort.update(status="needs-review", error=str(error), stopped=datetime.now(UTC).isoformat())
        plan.update(status="needs-review", error=str(error))
        atomic(plan_path, plan)
        atomic(marker, {"root": run_id, "status": "needs-review", "concepts": []})
        print(str(error), file=sys.stderr, flush=True)
        return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "run", "status"))
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--hub", type=Path, default=Path.home() / ".global-ai-hub")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--size", type=int, default=4, choices=range(1, 9))
    parser.add_argument("--max-cohorts", type=int)
    args = parser.parse_args(argv)
    if args.action == "plan":
        result = make_plan(args.repo, args.hub, args.source or args.hub / "concept-tree/RESEARCH_QUEUE_RANKED.md", args.size)
        atomic(args.plan, result)
        print(json.dumps({"rows": len(result["rows"]), "cohorts": len(result["cohorts"]),
                          "pending_concepts": sum(len(cohort["concepts"]) for cohort in result["cohorts"]),
                          "first": result["cohorts"][:1]}, indent=2))
        return 0
    if args.action == "status":
        result = json.loads(args.plan.read_text())
        print(json.dumps({key: result.get(key) for key in ("status", "pid", "error", "cohorts")}, indent=2))
        return 0
    return execute(args.repo, args.hub, args.plan, args.max_cohorts)


if __name__ == "__main__":
    raise SystemExit(main())
