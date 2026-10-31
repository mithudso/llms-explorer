#!/usr/bin/env python3
"""Plan and resume ranked /dr research in source-sharing cohorts.

Only `run` starts model calls. Plans preserve every ranked row, skip existing
checkouts, and group eligible concepts by parent. Each cohort uses Sol/medium,
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
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from html import unescape
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
    if isinstance(value, dict) and "rows" in value and "cohorts" in value:
        sync_row_outcomes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def sync_row_outcomes(plan):
    """Cohort checkpoints, including later completion receipts, own row status."""
    outcomes = {}
    for cohort in plan.get("cohorts", []):
        elsewhere = {key(name) for name in cohort.get("completed_elsewhere", [])}
        for name in cohort.get("concepts", []):
            outcomes[key(name)] = "complete" if key(name) in elsewhere else cohort["status"]
    for row in plan.get("rows", []):
        if key(row["concept"]) in outcomes:
            row["status"] = outcomes[key(row["concept"])]


def reviewed_gate_current(shared, cohort):
    """Only an independently verified current gate permits explicit review resume."""
    try:
        # Scope/owner reviews have no research run. load_manifest exits the
        # process for a missing run, so check before loading an optional one.
        if not (shared.run_dir(cohort["id"]) / "manifest.json").is_file():
            return False
        manifest = shared.load_manifest(cohort["id"])
        if not manifest.get("concepts") or any(row["status"] != "done" for row in manifest["concepts"]):
            return False
        shared.verify_current_gate(manifest)
        return True
    except (OSError, ValueError, KeyError):
        return False


def artifact_gate_current(manifest):
    """A stronger fresh gate must refresh an already-finalized projection."""
    if manifest.get("gate_contract_version") != 2:
        return True
    try:
        reference = manifest["codex_artifacts"]["canonical_artifact"]
        artifact = json.loads(Path(reference["path"]).read_text())
        packet = manifest["gate"]["packet_sha256"]
        return bool(packet and artifact["validation"]["packet_sha256"] == packet
                    and artifact["artifact_sha256"] == reference["sha256"])
    except (OSError, ValueError, KeyError, TypeError):
        return False


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
                     "concept": unescape("|".join(cells[3:-3])), "parent": unescape(cells[-3]),
                     "mode": cells[-2], "ranked_state": cells[-1]})
    return rows


def cohort_id(names, revisit=False):
    digest = hashlib.sha256(json.dumps(names).encode()).hexdigest()[:8]
    # Persist this identity in the plan. A new revisit plan must perform new
    # research, while resuming that same saved plan must keep its identity.
    return f"ranked-{digest}" + (f"-r{uuid.uuid4().hex[:8]}" if revisit else "")


def queue_parser(repo):
    path = repo / "scripts/mongodb_research_queue.py"
    return load("ranked_lossless_queue", path) if path.is_file() else None


def make_plan(repo, hub, source, size=4):
    ct = load("ranked_concept_tree", hub / "scripts/concept_tree.py")
    checkouts = load("ranked_checkouts", repo / "api/explorer_api/checkouts.py")
    _, held = checkouts._scan()
    nodes = ct.load_nodes(hub / "concept-tree/tree.json")
    names = {key(node["concept"]) for node in nodes}
    aliases = {key(alias) for node in nodes for alias in node.get("aliases", [])}
    parser = queue_parser(repo) or ct
    pending = {key(row["concept"]) for row in parser.load_queue(hub / "concept-tree/RESEARCH_QUEUE.md") if not row["done"]}
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
            cohorts.append({"id": cohort_id([row["concept"] for row in batch], any(row["mode"] == "revisit" for row in batch)), "parent": parent,
                            "concepts": [row["concept"] for row in batch],
                            "priority": min(row["rank"] for row in batch), "status": "pending",
                            "source_strategy": "Shared parent evidence, source-library FTS and cached snapshots; child-specific claims."})
    cohorts.sort(key=lambda cohort: cohort["priority"])
    return {"created": datetime.now(UTC).isoformat(), "source": str(source),
            "source_sha256": hashlib.sha256(text.encode()).hexdigest(), "model": "gpt-6.1-sol",
            "effort": "medium", "rows": rows, "cohorts": cohorts, "status": "planned"}


def run_command(command, log, env, timeout=7200):
    started = time.monotonic()
    process, cancelled, cleaning = None, None, False
    previous = {}
    def cancel(signum, frame):
        nonlocal cancelled
        cancelled = signum
        if process is not None and not cleaning:
            raise SystemExit(128 + signum)
    def stop():
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            return process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            return process.communicate()
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, cancel)
        if cancelled:
            raise SystemExit(128 + cancelled)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   env=env, start_new_session=True)
        if cancelled:
            raise SystemExit(128 + cancelled)
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        cleaning = True
        stdout, stderr = stop()
        with log.open("a") as stream:
            stream.write(json.dumps({"command": command, "timed_out": True, "stdout": stdout, "stderr": stderr}) + "\n")
        raise RuntimeError("Cohort phase exceeded its remaining time budget") from None
    except BaseException:
        if process is not None:
            cleaning = True
            stdout, stderr = stop()
            with log.open("a") as stream:
                stream.write(json.dumps({"command": command, "cancelled": True, "signal": cancelled,
                                         "stdout": stdout, "stderr": stderr}) + "\n")
        raise
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
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


def complete_queue(shared, hub, names, repo=None):
    with shared.locked(shared.RESEARCH_DIR / ".global.lock"):
        wanted = {key(name) for name in names}
        parser = queue_parser(repo or REPO)
        for root in dict.fromkeys(path for path in (hub, repo) if path is not None):
            queue = root / "concept-tree/RESEARCH_QUEUE.md"
            if not queue.exists():
                continue
            text = queue.read_text()
            if parser:
                lines = text.splitlines(keepends=True)
                for row in parser.load_queue(queue):
                    if not row["done"] and key(row["concept"]) in wanted:
                        index = row["line"] - 1
                        lines[index] = re.sub(r"^(\s*-\s*)\[ \]", r"\1[x]", lines[index], count=1)
                text = "".join(lines)
            else:
                pattern = re.compile(r"^(\s*-\s*)\[ \](\s*Concept:\s*`)([^`\n]+)(`[^\n]*)$", re.MULTILINE)
                text = pattern.sub(lambda match: (match[1] + "[x]" + match[2] + match[3] + match[4])
                                   if key(match[3]) in wanted else match[0], text)
            shared.atomic_write(queue, text)


def eligible_now(repo, hub, cohort, run_id, resume_names=()):
    checkouts = load("cohort_checkouts", repo / "api/explorer_api/checkouts.py")
    # The batch and its own /dr manifest are resumable holders of this work.
    own = {run_id, cohort["id"]}
    held = {key(name) for run in checkouts.runs() if run["name"] not in own for name in run["pending"]}
    ct = load("cohort_tree", hub / "scripts/concept_tree.py")
    parser = queue_parser(repo) or ct
    pending = {key(row["concept"]) for row in parser.load_queue(hub / "concept-tree/RESEARCH_QUEUE.md") if not row["done"]}
    nodes = ct.load_nodes(hub / "concept-tree/tree.json")
    covered = {key(name) for node in nodes for name in [node["concept"], *node.get("aliases", [])]}
    revisit = {key(row["concept"]) for row in cohort.get("rows", []) if row.get("mode") == "revisit"}
    resumable = {key(name) for name in resume_names}
    return [name for name in cohort["concepts"] if key(name) not in held and
            (key(name) in resumable or (key(name) in pending and (key(name) not in covered or key(name) in revisit)))]


def execute(repo, hub, plan_path, max_cohorts=None, retry_reviewed=False, cohort_ids=()):
    with (plan_path.parent / ".runner.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("This ranked plan already has a runner") from None
        return execute_locked(repo, hub, plan_path, max_cohorts, retry_reviewed=retry_reviewed, cohort_ids=cohort_ids)


def execute_all(repo, hub, plan_path):
    """Continue independent cohorts after dissent; never retry dissent unchanged."""
    with (plan_path.parent / ".runner.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("This ranked plan already has a runner") from None
        plan = json.loads(plan_path.read_text())
        plan["continue_on_review"] = True
        atomic(plan_path, plan)
        return _execute_all_locked(repo, hub, plan_path)


def _execute_all_locked(repo, hub, plan_path):
    while True:
        before = json.loads(plan_path.read_text())
        reviewed = {row["id"] for row in before["cohorts"] if row["status"] == "needs-review"}
        result = execute_locked(repo, hub, plan_path)
        after = json.loads(plan_path.read_text())
        new_reviews = {row["id"] for row in after["cohorts"] if row["status"] == "needs-review"} - reviewed
        pending = any(row["status"] not in ("complete", "skipped", "needs-review") for row in after["cohorts"])
        if not (result and new_reviews and pending):
            return result


def execute_locked(repo, hub, plan_path, max_cohorts=None, retry_reviewed=False, cohort_ids=()):
    plan = json.loads(plan_path.read_text())
    selected = set(cohort_ids)
    unknown = selected - {row["id"] for row in plan["cohorts"]}
    if unknown:
        raise ValueError("Unknown cohort selection: " + ", ".join(sorted(unknown)))
    run_id = plan_path.parent.name
    marker = Path(os.environ.get("LLMSX_HOME") or Path.home() / ".llmsx") / "jobs/batches" / run_id / "run.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    atomic(marker, {"root": run_id, "status": "in-progress",
                    "concepts": [name for cohort in plan["cohorts"] if cohort["status"] not in ("complete", "skipped") for name in cohort["concepts"]]})
    plan.update(status="running", pid=os.getpid(), started=datetime.now(UTC).isoformat())
    plan.pop("error", None)
    atomic(plan_path, plan)
    adapter = [sys.executable, str(repo / "scripts/codex_dr_run.py")]
    env = {**os.environ, "HUB_DIR": str(hub), "LLMS_EXPLORER_REPO": str(repo)}
    os.environ.update(HUB_DIR=str(hub), LLMS_EXPLORER_REPO=str(repo))
    completed = 0
    cohort = None
    try:
        shared = load("ranked_adapter", repo / "scripts/codex_dr_run.py").load_shared()
        for cohort in plan["cohorts"]:
            if selected and cohort["id"] not in selected:
                continue
            if cohort["status"] in ("complete", "skipped"):
                continue
            if cohort["status"] == "needs-review":
                if retry_reviewed:
                    if not reviewed_gate_current(shared, cohort):
                        continue
                elif plan.get("continue_on_review"):
                    continue
            cohort["rows"] = [row for row in plan["rows"] if row["concept"] in cohort["concepts"]]
            if (plan_path.parent / "STOP").exists() or (max_cohorts is not None and completed >= max_cohorts):
                break
            # Recheck other holders immediately before dispatch. The local batch
            # marker reserves this plan, so ignore only this plan's own label.
            previous_path = shared.run_dir(cohort["id"]) / "manifest.json"
            previous = shared.load_manifest(cohort["id"]) if previous_path.is_file() else {}
            resume_names = ([row["name"] for row in previous.get("concepts", []) if row["status"] == "done"]
                            if previous.get("ranked_queue_source") == str(plan_path) else [])
            picked = eligible_now(repo, hub, cohort, run_id, resume_names)
            if resume_names and any(name not in picked for name in resume_names):
                raise RuntimeError("A resumable cohort concept is held by another run")
            if not picked:
                cohort.update(status="skipped", note="No eligible concepts remain after checking coverage and other holders.")
                atomic(plan_path, plan)
                continue
            cohort.update(status="running", started=datetime.now(UTC).isoformat())
            cohort.pop("error", None)
            cohort.pop("stopped", None)
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
            if cohort.get("materials") or cohort.get("parents") or cohort.get("scopes"):
                with shared.run_lock(slug):
                    manifest["cohort_source_materials"] = cohort.get("materials", [])
                    manifest["cohort_source_family"] = cohort.get("source_family")
                    manifest["cohort_parents"] = {name: cohort["parents"][name] for name in picked
                                                   if name in cohort.get("parents", {})}
                    manifest["cohort_scopes"] = {name: cohort["scopes"][name] for name in picked
                                                  if name in cohort.get("scopes", {})}
                    shared.save_manifest(manifest)
            # A resumed manifest owns its original subset. Newly available
            # concepts need their own research and gate, never its completion.
            manifest_names = [row["name"] for row in manifest["concepts"]]
            if not manifest_names:
                raise RuntimeError("A cohort manifest has no researched concepts")
            manifest_keys = {key(name) for name in manifest_names}
            extra = [name for name in picked if key(name) not in manifest_keys]
            if extra:
                continuation = {**cohort, "id": cohort_id(extra, revisit=True),
                                "concepts": extra, "status": "pending", "continuation_of": slug}
                for field in ("error", "started", "finished", "stopped", "run", "deferred_to"):
                    continuation.pop(field, None)
                plan["cohorts"].insert(plan["cohorts"].index(cohort) + 1, continuation)
                cohort["deferred_to"] = continuation["id"]
            picked_keys = {key(value) for value in picked}
            if any(key(name) not in picked_keys for name in manifest_names):
                raise RuntimeError("A manifest concept is no longer eligible for this cohort")
            if cohort["concepts"] != manifest_names:
                cohort.setdefault("planned_concepts", cohort["concepts"])
                cohort["concepts"] = manifest_names
            picked = manifest_names
            atomic(plan_path, plan)
            # Include pages saved by earlier /dr runs in the shared FTS index.
            phase([sys.executable, str(hub / "scripts/source_library.py"), "reconcile"], 300)
            if manifest["status"] == "finalized" and not artifact_gate_current(manifest):
                # Native refresh reopens only manifest lifecycle fields. Claims,
                # accepted artifacts and every paid attempt stay in place.
                phase(adapter + ["init", parent, "--slug", slug, "--refresh"])
                manifest = shared.load_manifest(slug)
            if manifest["status"] != "finalized" or not artifact_gate_current(manifest):
                strict = manifest.get("gate_contract_version") == 2
                checkpoints = load("research_checkpoints", repo / "scripts/research_checkpoints.py") if strict else None
                stages = shared.run_dir(slug) / "checkpoints/stages.json"
                claim_paths = [shared.run_dir(slug) / "claims" / (c["slug"] + ".json") for c in manifest["concepts"]]
                if any(c["status"] != "done" for c in manifest["concepts"]):
                    phase(adapter + ["research", slug, "--max-parallel", "4"])
                manifest = shared.load_manifest(slug)
                errors = []
                current_claims = shared.load_claims(slug, errors)
                if errors or any(concept["status"] != "done" for concept in manifest["concepts"]):
                    raise RuntimeError(f"cohort has blocked or invalid claims: {errors}")
                if strict:
                    checkpoints.run_stage(stages, "research", current_claims, claim_paths, lambda: None)
                output = repo / ".agents/skills" / slug / "SKILL.md"
                render_command = adapter + ["render", slug, "--kind", "standalone", "--out", str(output),
                                      "--description", f"Explain {parent} through source-anchored concept research. TRIGGER: {parent}. SKIP: unrelated topics.",
                                      "--keywords", "research,concepts,reference,sources,mechanism,limits,operations,validation"]
                if strict:
                    checkpoints.run_stage(stages, "render", current_claims, [output], lambda command=render_command: phase(command))
                else:
                    phase(render_command)
                gate_current = False
                if strict:
                    try:
                        shared.verify_current_gate(manifest)
                        gate_current = True
                    except (ValueError, OSError, KeyError):
                        receipt = manifest.get("gate", {})
                        if "non-supported" in (receipt.get("error") or ""):
                            packet = json.loads((shared.run_dir(slug) / receipt["attempt"] / "packet.json").read_text())
                            # The gate's canonical digest uses compact JSON.
                            now = {k: hashlib.sha256(json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
                                   for k, v in current_claims.items()}
                            if packet["inputs"] == now:
                                raise RuntimeError("Substantive gate dissent requires reviewed claim correction") from None
                if not gate_current:
                    phase(adapter + ["gate", slug, "--model", "gpt-6.1-sol", "--effort", "medium"], 1200)
                if strict:
                    manifest = shared.load_manifest(slug)
                    shared.verify_current_gate(manifest)
                    gate_inputs = {"claims": current_claims, "gate_packet_sha256": manifest["gate"]["packet_sha256"]}
                    checkpoints.run_stage(stages, "gate", gate_inputs, [shared.run_dir(slug) / "gate.json"], lambda: None)
                gate = json.loads((shared.run_dir(slug) / "gate.json").read_text())
                if not gate.get("verdicts"):
                    raise RuntimeError("Blind claim gate returned no verdicts")
                dissent = [row for row in gate["verdicts"] if row.get("verdict") != "SUPPORTED"]
                if dissent:
                    raise RuntimeError(f"blind claim gate needs review: {len(dissent)} non-supported verdicts")
                finish_command = adapter + ["finish", slug, "--status", "COMPLETED", "--stop-reason", "Ranked source-sharing cohort; scout and blind gate completed."]
                if strict:
                    checkpoints.run_stage(stages, "export", gate_inputs, [shared.run_dir(slug) / "artifacts/receipt.json"], lambda command=finish_command: phase(command))
                else:
                    phase(finish_command)
            manifest = shared.load_manifest(slug)
            errors = []
            documents = shared.load_claims(slug, errors)
            if errors or any(row["status"] != "done" or row["slug"] not in documents
                             or documents[row["slug"]].get("slug", row["slug"]) != row["slug"]
                             for row in manifest["concepts"]):
                raise RuntimeError(f"cohort completion requires validated manifest claims: {errors}")
            # A completed run with a failed website write can resume without
            # repeating paid research. This also checks all four website surfaces.
            complete_queue(shared, hub, picked, repo)
            site_command = [sys.executable, str(repo / "scripts/research_site_sync.py"), "--repo", str(repo), "--hub", str(hub), "--apply"]
            if manifest.get("gate_contract_version") == 2:
                checkpoints = load("research_checkpoints", repo / "scripts/research_checkpoints.py")
                publication_inputs = {"claims": documents, "gate_packet_sha256": manifest["gate"]["packet_sha256"]}
                checkpoints.run_stage(shared.run_dir(slug) / "checkpoints/stages.json", "local-publication", publication_inputs,
                    [repo / "site/src/data/tree.json", repo / "site/src/data/context.json", repo / "site/src/data/concepts"],
                    lambda command=site_command: phase(command, 600))
            else:
                phase(site_command, 600)
            for name in picked:
                with (marker.parent / "results.jsonl").open("a") as stream:
                    stream.write(json.dumps({"concept": name, "status": "complete", "run": slug}) + "\n")
            cohort.update(status="complete", finished=datetime.now(UTC).isoformat(), run=str(shared.run_dir(slug)))
            completed += 1
            atomic(plan_path, plan)
            print(json.dumps({"cohort": slug, "status": "complete", "concepts": picked}), flush=True)
        plan["status"] = ("complete" if all(cohort["status"] in ("complete", "skipped") for cohort in plan["cohorts"])
                          else "needs-review" if any(cohort["status"] == "needs-review" for cohort in plan["cohorts"])
                          else "stopped")
        atomic(plan_path, plan)
        atomic(marker, {"root": run_id, "status": plan["status"], "concepts": []})
        return 0
    except (KeyboardInterrupt, SystemExit):
        if cohort is not None and cohort["status"] not in ("complete", "skipped"):
            cohort.update(status="cancelled", stopped=datetime.now(UTC).isoformat())
        plan.update(status="cancelled")
        atomic(plan_path, plan)
        atomic(marker, {"root": run_id, "status": "cancelled", "concepts": []})
        raise
    except Exception as error:  # noqa: BLE001 — release reservations for every setup or phase failure.
        if cohort is not None:
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
    parser.add_argument("--cohort", action="append", default=[],
                        help="Run only this exact cohort ID; repeat to select several")
    parser.add_argument("--continue-on-review", action="store_true",
                        help="Keep evidence dissent withheld and process independent remaining cohorts")
    parser.add_argument("--retry-reviewed", action="store_true",
                        help="Resume withheld cohorts only after their current independent gates pass")
    args = parser.parse_args(argv)
    if args.retry_reviewed and (args.action != "run" or args.continue_on_review):
        parser.error("--retry-reviewed requires run and cannot combine with --continue-on-review")
    if args.cohort and (args.action != "run" or args.continue_on_review):
        parser.error("--cohort requires run and cannot combine with --continue-on-review")
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
    if args.continue_on_review:
        if args.max_cohorts is not None:
            parser.error("--continue-on-review cannot be combined with --max-cohorts")
        return execute_all(args.repo, args.hub, args.plan)
    return execute(args.repo, args.hub, args.plan, args.max_cohorts,
                   retry_reviewed=args.retry_reviewed, cohort_ids=args.cohort)


if __name__ == "__main__":
    raise SystemExit(main())
