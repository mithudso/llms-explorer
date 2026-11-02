#!/usr/bin/env python3
"""Freeze an exhaustive MongoDB inventory into a resumable private DR plan."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def make_plan(inventory, *, created=None, execution_labels=None):
    """Account for every identity without applying a minimum CVS threshold."""
    rows, cohorts, assignments = [], [], {}
    execution_labels = execution_labels or {}
    by_id = {row["id"]: row for row in inventory["rows"]}
    if len(by_id) != len(inventory["rows"]):
        raise ValueError("Inventory identities must be unique")
    if set(execution_labels) - set(by_id):
        raise ValueError("Execution labels must identify an inventory row")
    for identity, label in execution_labels.items():
        if " ".join(label.split()).casefold() != " ".join(by_id[identity]["concept"].split()).casefold():
            raise ValueError("Execution labels may only preserve case or whitespace variants")
    gaps = set(inventory["gaps"])
    if any(row["cvs"] is None for row in by_id.values() if row["id"] in gaps):
        raise ValueError("Every research candidate needs a CVS assessment")
    seen = set()
    for group in inventory["cohorts"]:
        buckets = {}
        for identity in group["row_ids"]:
            if identity in seen:
                raise ValueError("An inventory row has multiple cohort assignments")
            seen.add(identity)
            row = by_id[identity]
            axes = (row.get("score") or {}).get("axes") or row.get("score") or {}
            hard_gate = axes.get("viability", axes.get("via", 5)) <= 1 or axes.get("novelty", axes.get("nov", 1)) == 0
            status = "skipped" if identity not in gaps else "needs-review" if hard_gate else "pending"
            buckets.setdefault(status, []).append(row)
        for status, members in buckets.items():
            members.sort(key=lambda row: row["rank"])
            cid = group["id"] + ("-" + status if len(buckets) > 1 else "")
            parents = {execution_labels.get(row["id"], row["concept"]):
                       (row["parents"][0] if row["parents"] else "MongoDB") for row in members}
            names = [execution_labels.get(row["id"], row["concept"]) for row in members]
            cohort = {"id": cid, "inventory_cohort": group["id"], "concepts": names,
                      "planned_concepts": names[:], "parents": parents, "parent": parents[names[0]],
                      "source_family": group["source_family"], "source_affinity": group["source_affinity"],
                      "materials": group["likely_source_materials"], "source_strategy": group["source_strategy"],
                      "priority": min(row["rank"] for row in members), "status": status}
            if status == "skipped":
                cohort["note"] = "Existing sourced coverage; retained for exhaustive accounting."
            elif status == "needs-review":
                cohort["note"] = "CFE novelty=0 or viability<=1; review scope or sources before paid research."
            cohorts.append(cohort)
            for original in members:
                name = execution_labels.get(original["id"], original["concept"])
                if name in assignments:
                    raise ValueError("Canonical concept names must be unique")
                assignments[name] = cid
                rows.append({"id": original["id"], "concept": name, "canonical_concept": original["concept"],
                             "rank": original["rank"],
                             "cvs": original["cvs"], "decision": original["decision"],
                             "mode": "revisit" if original["coverage_category"] != "frontier" else "new",
                             "parent": parents[name], "parents": original["parents"],
                             "inventory_cohort": group["id"], "cohort_id": cid,
                             "coverage_category": original["coverage_category"],
                             "initial_status": status, "score": original.get("score"),
                             "reservation_holder_at_plan": original.get("reservation_holder"),
                             "original_labels": original.get("original_labels", [name])})
    if seen != set(by_id):
        raise ValueError("Every inventory row must have a cohort assignment")
    cohorts.sort(key=lambda cohort: (cohort["priority"], cohort["id"]))
    rows.sort(key=lambda row: row["rank"])
    fingerprint = hashlib.sha256(json.dumps(inventory, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"schema": "mongodb-dr-plan/v1", "plan_id": "mongodb-" + fingerprint[:20],
            "created": created or datetime.now(UTC).isoformat(), "domain": "mongodb",
            "inventory_sha256": fingerprint, "model": "gpt-6.1-sol", "effort": "medium",
            "gate_model": "gpt-6.1-sol", "gate_effort": "medium", "status": "planned",
            "scope": "Run-start backlog; new descendants remain a separate backlog.",
            "rows": rows, "cohorts": cohorts, "handoff_assignments": assignments}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--execution-labels", type=Path, help="Private exact legacy case/whitespace labels keyed by inventory id")
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("Refusing to replace a frozen plan; resume the existing plan")
    labels = json.loads(args.execution_labels.read_text()) if args.execution_labels else None
    plan = make_plan(json.loads(args.inventory.read_text()), execution_labels=labels)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        stream.write(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"plan_id": plan["plan_id"], "rows": len(plan["rows"]),
                      "cohorts": len(plan["cohorts"]),
                      "pending": sum(len(c["concepts"]) for c in plan["cohorts"] if c["status"] == "pending"),
                      "review": sum(len(c["concepts"]) for c in plan["cohorts"] if c["status"] == "needs-review")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
