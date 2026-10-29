#!/usr/bin/env python3
"""Reconcile queue identities and saved outcomes without running research.

Default: report only. --apply preserves preimages and checks current input hashes.
Existing tree membership never establishes a research completion.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import re
from collections import defaultdict
from contextlib import ExitStack
from html import escape
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def key(name):
    return " ".join(name.split()).casefold()


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code(value):
    ticks = "`" * (max((len(x) for x in re.findall(r"`+", value)), default=0) + 1)
    padding = " " if value.startswith("`") or value.endswith("`") else ""
    return ticks + padding + value + padding + ticks


def tag(line, name, value):
    pattern = re.compile(r"\|\s*" + re.escape(name) + r":\s*(`+).*?\1(?=\s*(?:\||$))", re.IGNORECASE)
    replacement = "| " + name + ": " + code(value)
    return pattern.sub(lambda match: replacement, line, count=1) if pattern.search(line) else line + " " + replacement


def reconcile_queue(text, rows, nodes, held, completed, old_modes=None):
    """Deduplicate identities, retain parent edges, and make review intent explicit."""
    old_modes = old_modes or {}
    named = {key(node["concept"]): node for node in nodes}
    aliases = {key(alias): node for node in nodes for alias in node.get("aliases", [])}
    groups = defaultdict(list)
    for row in rows:
        groups[key(row["concept"])].append(row)
    lines = text.splitlines(keepends=True)
    changes, additional_edges = [], []
    for identity, occurrences in groups.items():
        pending = any(not row["done"] for row in occurrences)
        done = all(row["done"] for row in occurrences)
        state = None
        if pending and identity in held:
            done, state = False, "held-review" if identity in named or any(row["done"] for row in occurrences) else "held"
        elif identity in completed:
            done = True
        elif pending and (identity in named or identity in aliases):
            done, state = False, "coverage-review"
        parents = []
        for row in occurrences:
            parent = row.get("parentConcept")
            if parent:
                owner = named.get(key(parent)) or aliases.get(key(parent))
                canonical = owner["concept"] if owner else parent
                if canonical not in parents:
                    parents.append(canonical)
        primary = occurrences[0]
        line = primary["raw"]
        line = re.sub(r"^(\s*-\s*)\[[ xX]\]", lambda match, done=done: match[1] + ("[x]" if done else "[ ]"), line, count=1)
        if parents:
            line = tag(line, "Parent", parents[0])
            if len(occurrences) > 1 or parents[0] != primary.get("parentConcept"):
                for parent in parents:
                    additional_edges.append((parent, primary["concept"]))
        if len(parents) > 1:
            line = tag(line, "Also-parent", "; ".join(parents[1:]))
        if state:
            line = tag(line, "Queue-state", state)
        elif done and "queue-state" in primary.get("tags", {}):
            line = tag(line, "Queue-state", "complete")
        mode = primary.get("tags", {}).get("mode") or old_modes.get(identity)
        if state == "held-review":
            mode = "revisit"
        if mode and mode != "—":
            line = tag(line, "Mode", mode)
        if any(row["done"] for row in occurrences) and not done:
            line = tag(line, "Prior-completion", "recorded; current reservation retained")
        if len(occurrences) > 1:
            line = tag(line, "Previous-records", "; ".join(row["raw"] for row in occurrences[1:]))
            changes.append({"concept": primary["concept"], "removed_duplicates": len(occurrences) - 1,
                            "done": done, "parents": parents})
        lines[primary["line"] - 1] = line + ("\n" if lines[primary["line"] - 1].endswith("\n") else "")
        for duplicate in occurrences[1:]:
            lines[duplicate["line"] - 1] = ""
    return "".join(lines), additional_edges, changes


def verified_completions(hub, plans, shared, artifact):
    """Use saved contracts, preserving accepted historical legacy results."""
    completed, access = {}, {}
    for plan in plans.values():
        for cohort in plan["cohorts"]:
            run = hub / "research" / cohort["id"]
            manifest_path = run / "manifest.json"
            access[cohort["id"]] = "available" if manifest_path.is_file() else "unavailable-local"
            if not manifest_path.is_file():
                continue
            manifest = read(manifest_path)
            if manifest.get("status") != "finalized" or any(row["status"] != "done" for row in manifest.get("concepts", [])):
                continue
            receipt_path = run / "artifacts/receipt.json"
            receipt = read(receipt_path) if receipt_path.is_file() else {}
            if not receipt.get("ok"):
                continue
            if manifest.get("gate_contract_version") == 2:
                shared.verify_current_gate(manifest)
                canonical = receipt.get("canonical_artifact", {}).get("path")
                if not canonical:
                    continue
                artifact.verify(read(Path(canonical)))
            else:
                # This records an existing accepted legacy outcome; it does not
                # recertify it as v2 or accept a previously unfinished run.
                access[cohort["id"]] = "available-historical-legacy"
                if cohort["status"] != "complete":
                    continue
            for concept in manifest["concepts"]:
                completed[key(concept["name"])] = cohort["id"]
    return completed, access


def reconcile_plans(plans, completed, access, ranked):
    result = copy.deepcopy(plans)
    for plan in result.values():
        for cohort in plan["cohorts"]:
            cohort["evidence_access"] = access.get(cohort["id"], "unavailable-local")
            if cohort["concepts"] and all(completed.get(key(name)) == cohort["id"] for name in cohort["concepts"]):
                cohort["status"] = "complete"
                if cohort.get("error"):
                    cohort["previous_review_error"] = cohort.pop("error")
            if cohort["status"] in ("pending", "stopped", "cancelled"):
                elsewhere = [name for name in cohort["concepts"]
                             if key(name) in completed and completed[key(name)] != cohort["id"]]
                if elsewhere:
                    cohort["completed_elsewhere"] = elsewhere
                    cohort["completion_receipts"] = {name: completed[key(name)] for name in elsewhere}
                if len(elsewhere) == len(cohort["concepts"]):
                    cohort["status"] = "skipped"
                    cohort["note"] = "All original concepts completed in later verified cohorts."
        ranked.sync_row_outcomes(plan)
        statuses = {cohort["status"] for cohort in plan["cohorts"]}
        plan["status"] = ("complete" if statuses <= {"complete", "skipped"}
                          else "needs-review" if "needs-review" in statuses else "stopped")
        if "pid" in plan:
            plan["last_runner_pid"] = plan.pop("pid")
        if "needs-review" not in statuses and plan.get("error"):
            plan["previous_review_error"] = plan.pop("error")
        plan["outcome_schema_version"] = 1
    return result


def ranked_view(rows, nodes, scores, held, outcomes, old_modes):
    named = {key(node["concept"]): node for node in nodes}
    aliases = {key(alias) for node in nodes for alias in node.get("aliases", [])}
    score_map = {key(name): value for name, value in scores.items()}
    records = []
    for row in rows:
        if row["done"]:
            continue
        identity = key(row["concept"])
        node = named.get(identity, {})
        score = node.get("cvs", score_map.get(identity, {}).get("cvs"))
        if score is None:
            value = row.get("tags", {}).get("cvs")
            score = float(value) if value else None
        state = "frontier"
        decision = "UNSCORED" if score is None else "RESEARCH" if score >= 3.2 else "BELOW-GATE"
        if identity in held:
            state, decision = "held", "HELD"
        elif outcomes.get(identity) == "needs-review":
            state, decision = "repair-required", "REPAIR"
        elif identity in named or identity in aliases:
            state, decision = "coverage-review", "REVIEW"
        records.append({"concept": row["concept"], "score": score, "state": state, "decision": decision,
                        "parent": row.get("parentConcept") or "—",
                        "mode": row.get("tags", {}).get("mode") or old_modes.get(identity) or "—"})
    records.sort(key=lambda row: (-(row["score"] if row["score"] is not None else -1), key(row["concept"])))
    lines = ["# Research queue, ranked by Concept Viability Score", "",
             "Generated from the live hub queue and saved cohort outcomes. This is a view; the queue remains the source of truth.",
             "Held, repair-required and coverage-review rows require their existing workflow; they are not fresh-discovery assignments.",
             f"Pending unique concepts: **{len(records)}**. Score gate: **3.2**. Repository frontier coverage remains separate.", "",
             "| # | CVS | decision | concept | parent | mode | tree state |",
             "|---:|---:|---|---|---|---|---|"]
    for index, row in enumerate(records, 1):
        score = f"{row['score']:.2f}" if row['score'] is not None else "—"
        name, parent = (escape(row[field], quote=False).replace("|", "&#124;") for field in ("concept", "parent"))
        lines.append(f"| {index} | {score} | {row['decision']} | {name} | {parent} | {row['mode']} | {row['state']} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--hub", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--backup-dir", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if args.apply and not args.backup_dir:
        parser.error("--apply requires --backup-dir")
    repo, hub = args.repo.resolve(), args.hub.resolve()
    queue = load("queue_reconciliation_parser", repo / "scripts/mongodb_research_queue.py")
    ranked = load("queue_reconciliation_ranked", repo / "scripts/codex_ranked_research.py")
    checkouts = load("queue_reconciliation_holders", repo / "api/explorer_api/checkouts.py")
    shared = load("queue_reconciliation_adapter", repo / "scripts/codex_dr_run.py").load_shared()
    artifact = load("queue_reconciliation_artifact", repo / "scripts/research_artifact.py")
    tree = load("queue_reconciliation_tree", repo / "hub/scripts/concept_tree.py")
    _, held = checkouts._scan()
    decisions = read(args.decisions)
    plan_paths = sorted((hub / "research/.ranked").glob("*/plan.json"))
    input_paths = [*plan_paths, args.decisions,
                   hub / "concept-tree/cvs-scores.json",
                   *(root / "concept-tree" / name for root in (hub, repo)
                     for name in ("tree.json", "RESEARCH_QUEUE.md", "RESEARCH_QUEUE_RANKED.md"))]
    hashes = {path: digest(path) if path.is_file() else None for path in input_paths}
    plans = {str(path): read(path) for path in plan_paths}
    completed, access = verified_completions(hub, plans, shared, artifact)
    updated_plans = reconcile_plans(plans, completed, access, ranked)
    old_rank = hub / "concept-tree/RESEARCH_QUEUE_RANKED.md"
    old_modes = {key(row["concept"]): row["mode"] for row in ranked.ranked_rows(old_rank.read_text())
                 if row["mode"] == "revisit"}
    changes, report = {}, {"version": "1.0.0", "queues": {}, "held_concepts": len(held),
                                      "completion_receipts": len(completed), "evidence_access": access}
    tree_sets = {}
    for root in (hub, repo):
        path = root / "concept-tree/tree.json"
        nodes = read(path)
        baseline_errors = set(tree.ConceptTree(nodes).validate())
        named = {node["concept"]: node for node in nodes}
        alias_owners = {key(alias): node["concept"] for node in nodes for alias in node.get("aliases", [])}
        for mapping in decisions.get("aliases", []):
            if mapping["concept"] in named:
                owner = named[mapping["concept"]]
                if mapping["alias"] in named and mapping["alias"] != owner["concept"]:
                    raise ValueError("alias would hide a distinct node: " + mapping["alias"])
                if alias_owners.get(key(mapping["alias"]), owner["concept"]) != owner["concept"]:
                    raise ValueError("alias belongs to another node: " + mapping["alias"])
                owner["aliases"] = list(dict.fromkeys([*owner.get("aliases", []), mapping["alias"]]))
        tree_sets[root] = nodes
        queue_path = root / "concept-tree/RESEARCH_QUEUE.md"
        text, edges, duplicates = reconcile_queue(queue_path.read_text(), queue.load_queue(queue_path), nodes,
                                                  held, completed, old_modes)
        for parent, child in edges:
            if parent in named:
                named[parent]["childConcepts"] = list(dict.fromkeys([*named[parent].get("childConcepts", []), child]))
        added_errors = set(tree.ConceptTree(nodes).validate()) - baseline_errors
        if added_errors:
            raise ValueError("queue reconciliation adds tree problems: " + "; ".join(sorted(added_errors)))
        changes[queue_path] = text
        changes[path] = json.dumps(nodes, indent=2, ensure_ascii=False) + "\n"
        report["queues"][str(root)] = {"duplicate_groups_reconciled": duplicates}
    for path, plan in updated_plans.items():
        changes[Path(path)] = json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
    # Parse the planned queue through a private scratch file, never mutate live
    # state to compute a view.
    scratch = args.report.parent / (args.report.stem + "-queue-scratch.md")
    scratch.parent.mkdir(parents=True, exist_ok=True)
    scratch.write_text(changes[hub / "concept-tree/RESEARCH_QUEUE.md"])
    try:
        rows = queue.load_queue(scratch)
    finally:
        scratch.unlink()
    outcomes = {key(row["concept"]): row["status"] for plan in updated_plans.values() for row in plan["rows"]}
    view = ranked_view(rows, tree_sets[hub], read(hub / "concept-tree/cvs-scores.json"), held, outcomes, old_modes)
    for root in (hub, repo):
        changes[root / "concept-tree/RESEARCH_QUEUE_RANKED.md"] = view
    changes = {path: text for path, text in changes.items() if not path.is_file() or path.read_text() != text}
    report["changes"] = [str(path) for path in changes]
    report["applied"] = args.apply
    if args.apply:
        args.backup_dir.mkdir(parents=True, exist_ok=False)
        transaction = load("queue_reconciliation_transaction", repo / "scripts/research_transaction.py")
        with ExitStack() as locks:
            for path in plan_paths:
                runner = locks.enter_context((path.parent / ".runner.lock").open("a"))
                fcntl.flock(runner, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock = locks.enter_context((hub / "research/.global.lock").open("a"))
            fcntl.flock(lock, fcntl.LOCK_EX)
            for path, expected in hashes.items():
                if (digest(path) if path.is_file() else None) != expected:
                    raise ValueError("input changed during reconciliation: " + str(path))
            tx = transaction.Transaction(args.backup_dir, registry=transaction.registry_dir(hub / "research"))
            try:
                for path, text in changes.items():
                    tx.write(path, text)
                tx.commit()
            except BaseException:
                tx.rollback()
                raise
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"changed_files": len(changes), "held_concepts": len(held), "applied": args.apply}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
