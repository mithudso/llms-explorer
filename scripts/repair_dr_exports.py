#!/usr/bin/env python3
"""Restore complete authored DR exports and sanitize repository copies.

Default: read-only plan. --apply backs up every change and refreshes the website.
This uses existing units, never new model calls or a narrower historical run.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import re
import shutil
import sys
import tempfile
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def plan(repo: Path, hub: Path, withheld=()):
    sys.path.insert(0, str(repo / "scripts"))
    from codex_dr_artifacts import (
        PACK_FILES,
        compile_rows,
        load_module,
        public_pack_files,
    )

    lca = load_module("repair_dr_lca", repo / ".claude/skills/llms-concept-abstractor/scripts/concept_abstract.py")
    website = load_module("repair_dr_website", repo / "scripts/research_site_sync.py")
    scrub = load_module("repair_dr_scrub", repo / "scripts/publish_scrub.py")
    trees = [website.nodes_at(root / "concept-tree/tree.json") for root in (hub, repo)]
    private = set()
    while True:
        found = set()
        for nodes in trees:
            found.update(scrub.filter_tree(nodes, scrub.gate.denylist(), private)[1])
        if found <= private:
            break
        private.update(found)
    private_slugs = {node["slug"] for nodes in trees for node in nodes if node["concept"] in private}
    roots = {"hub": hub / "llms-concepts", "repository": repo / "outputs/llms-concepts"}
    jobs = [(label, path) for label, root in roots.items() for path in sorted(root.glob("*.llms"))]
    # A missing repository peer may be filled, but an existing peer always uses
    # its own units. It may contain fuller or newer research than the hub copy.
    jobs.extend(("repository", path) for path in sorted(roots["hub"].glob("*.llms"))
                if not (roots["repository"] / path.name).exists())
    writes, repaired, skipped = {}, [], []
    with tempfile.TemporaryDirectory(prefix="repair-authored-dr-") as temporary:
        for number, (label, source) in enumerate(jobs):
            if not (source / "manifest.json").is_file() or not (source / "units.jsonl").is_file():
                continue
            metadata = json.loads((source / "manifest.json").read_text())
            rows = [json.loads(line) for line in (source / "units.jsonl").read_text().splitlines() if line.strip()]
            if not rows or any(row.get("origin") != "dr" for row in rows):
                continue
            destination = roots[label] / source.name
            if label == "repository" and (metadata["concept"] in private or metadata["slug"] in private_slugs
                    or scrub._matches(metadata["concept"] + " " + metadata["slug"], scrub.gate.denylist())):
                if destination.is_dir():
                    writes.update({path: None for path in destination.rglob("*") if path.is_file()})
                skipped.append({"pack": source.name, "reason": "private repository destination"})
                continue
            if any(not (source / name).is_file() for name in PACK_FILES):
                skipped.append({"pack": source.name, "reason": "incomplete original pack"})
                continue
            files = {name: (source / name).read_text() for name in PACK_FILES}
            missing = [row for row in rows if re.sub(r"\s+", " ", row["text"]).strip() not in files["llms-full.txt"]]
            if missing:
                compiled = Path(temporary) / str(number)
                compile_rows(lca, compiled, metadata["concept"], metadata["slug"], rows, metadata)
                files = {name: (compiled / name).read_text() for name in PACK_FILES}
            if label == "repository":
                files = public_pack_files(repo, hub, files, lca, withheld)
            changed = {destination / name: text for name, text in files.items()
                       if not (destination / name).is_file() or (destination / name).read_text() != text}
            if changed:
                writes.update(changed)
                repaired.append({"target": label, "pack": source.name, "claims": len(rows),
                                 "restored_claims": len(missing), "generated": metadata["generated"]})
    return {"packs": repaired, "skipped": skipped, "changed_files": [str(path) for path in writes]}, writes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--hub", type=Path, default=Path.home() / ".global-ai-hub")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    with ExitStack() as stack:
        for path in (args.hub / "research/.global.lock", args.repo / "tmp/research-site-sync.lock"):
            path.parent.mkdir(parents=True, exist_ok=True)
            fcntl.flock(stack.enter_context(path.open("a")), fcntl.LOCK_EX)
        report, writes = plan(args.repo, args.hub)
        if args.apply:
            sys.path.insert(0, str(args.repo / "scripts"))
            from public_research_references import resolve
            reference_writes, withheld = resolve(args.repo, args.hub, writes)
            report, writes = plan(args.repo, args.hub, withheld)
            writes.update(reference_writes)
            backup = args.repo / "tmp/dr-export-repair-backups" / datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
            for path in writes:
                if path.is_file():
                    label, root = ("repository", args.repo) if path.is_relative_to(args.repo) else ("hub", args.hub)
                    saved = backup / label / path.relative_to(root)
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, saved)
            for path, text in writes.items():
                if text is None:
                    path.unlink(missing_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    staging = path.with_name(path.name + ".dr-repair-tmp")
                    staging.write_text(text)
                    staging.replace(path)
            report.update(backup=str(backup), changed_files=[str(path) for path in writes])
    if args.apply:
        from research_site_sync import sync
        report["website"] = sync(args.repo, args.hub, apply=True)
        receipt = args.repo / "tmp/dr-export-repair-last.json"
        receipt.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"applied": args.apply, "packs_changed": len(report["packs"]),
                      "hub_claims_restored": sum(row["restored_claims"] for row in report["packs"] if row["target"] == "hub"),
                      "changed_files": len(report["changed_files"]), "skipped": len(report["skipped"])}))
    return 1 if args.check and writes else 0


if __name__ == "__main__":
    raise SystemExit(main())
